<?php

require_once "HtmlPrinter.php";

// strings to store generated tables for tests
$parserTable = HtmlPrinter::getParserTableHeader();
$fileTable = HtmlPrinter::getFileTableHeader();
$interpretTable = HtmlPrinter::getInterpreterTableHeader();
$overallTable = HtmlPrinter::getOverallTableHeader();

// default test settings use both
$interpretOnly = false;
$parserOnly = false;
$both = false;

$parserPath = "./parse.php";
$interpretPath = "./interpret.py";
$recursiveSearch = false;
$noclean = true;
$fileIterator = null;
$testCounter = 0;
$failedTestCounter = 0;
$passedTestCounter = 0;

//configs
$xmlLibPath = "/pub/courses/ipp/jexamxml/jexamxml.jar";
$xmlConfigPath = "/pub/courses/ipp/jexamxml/options";
$testPath = "./";

testSetUp();
testRun();
testTearDown();

function printHelp() {
    echo "\n";
    echo "AVAILABLE ARGUMENTS:\n";
    echo "\t--directory='path'\tset path to test directory\n";
    echo "\t--recursive\t\trecursive test search\n";
    echo "\t--parse-script='file'\tpath to a tested parser script, default location is './parse.php'\n";
    echo "\t--int-script=file\tpath to a tested interpreter script, default location is './interpret.php'\n";
    echo "\t--parse-only\t\tonly parser will be tested\n";
    echo "\t--int-only\t\tonly interpreter will be tested\n";
    echo "\t--jexampath='path'\tpath to dir containing JExamXML java executable and its options file\n";
    exit(0);
}

function errorHandle($errMessage) {
    fprintf(STDERR, $errMessage);
    exit(41);
}

// processing given arguments
function testSetUp() {
    global $parserOnly, $parserPath, $interpretOnly, $interpretPath, $testPath, $recursiveSearch, $xmlLibPath, $xmlConfigPath, $parserTable, $interpretTable, $noclean;

    $getopt = getopt("", long_options: array("help", "parse-only", "interpret-only", "int-only", "jexampath:", "int-script:", "parse-script:", "recursive", "directory:", "noclean"));
    //DEBUG var_dump($getopt);

    if (isset($getopt['help'])){
        printHelp();
    }
    if (isset($getopt['parse-only'])){
            $parserOnly = true;
            $interpretTable = null;
    }
    if (isset($getopt['int-only'])){
            $interpretOnly = true;
            $parserTable = null;
    }
    if (isset($getopt['parse-script'])){
        $parserPath = $getopt['parse-script'];

        if ($interpretOnly) {
            errorHandle("Cannot combine interpret and parser commands.");
        }
    }
    if (isset($getopt['int-script'])){
        $interpretPath = $getopt['int-script'];

        if ($parserOnly) {
            errorHandle("Cannot combine interpret and parser commands.");
        }
    }
    if (isset($getopt['directory'])) {
        $testPath = $getopt['directory'];

        if(!is_dir($testPath))
        {
            errorHandle("Directory cannot be found\n");
        }
    }
    if (isset($getopt['recursive'])) {
        $recursiveSearch = true;
    }
    if (isset($getopt['noclean'])) {
        $noclean = false;
    }
    if (isset($getopt['jexampath'])) {
        $xmlLibPath = $getopt['jexampath'] . "jexamxml.jar";
        $xmlConfigPath = $getopt['jexampath'] . "options";
    }
    if ($parserOnly && $interpretOnly) {
        errorHandle("Cannot combine interpret and parser commands.");
    }

    setFileIterator($recursiveSearch, $testPath);
    HtmlPrinter::printHeader();
}

// sets file iterator based on argument if it is recursive or not
function setFileIterator($recursiveSearch, $testPath) {
    global $fileIterator;

    if ($recursiveSearch)
        $fileIterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator( $testPath ));
    else
        $fileIterator = new DirectoryIterator($testPath);
}

// creates missing files that are needed for testing and are missing
function checkAndReplaceMissingFiles($file, $dirPath) {
    if (!file_exists($ff = $dirPath . $file . ".rc")) {
        $newFile = fopen($ff, "w");
        fwrite($newFile, "0");
        fclose($newFile);
    }
    if (!file_exists($ff = $dirPath . $file . ".in")) {
        $newFile = fopen($ff, "w");
        fclose($newFile);
    }
    if (!file_exists($ff = $dirPath . $file . ".out")) {
        $newFile = fopen($ff, "w");
        fclose($newFile);
    }
}

// getting expected error code from .rc file
function getExpectedErrorCode($fileNameWithoutEtension, $dirPath) {
    $content = file_get_contents($dirPath . $fileNameWithoutEtension . ".rc");

    if (is_numeric($content)) {
        return (int)$content;
    } else {
        errorHandle("Cannot read '.rc' file");
    }
}

// parser only test
function parserTest($fileName, $dirPath, $expectedErr) {
    global $parserTable, $parserPath, $xmlLibPath, $xmlConfigPath, $passedTestCounter, $overallTable, $noclean;
    $codeCheckRes = "failed";
    $xmlRes = "passed";
    $outputXml = "tmpOut.xml";
    $delta = "delta.xml";
    $overall = "failed";

    // calls php with parse.php with needed inputs
    exec("php8.1 " . $parserPath . " < " . $dirPath . $fileName . ".src" . " > " . $dirPath . $outputXml, result_code: $resCode);

    // checks if expected error code is correct and based on that it either
    // checks the xml diff or sets test to failed
    if ($resCode == $expectedErr) {
        if ($expectedErr == 0) {
            exec("java -jar " . $xmlLibPath . " " . $dirPath . $outputXml . " " . $dirPath . $fileName . ".out" . " " . $dirPath . $delta . " " . $xmlConfigPath, result_code: $xmlResCode);
            if ($xmlResCode !== 0) {
                $xmlRes = "failed";
            }
        }
        $codeCheckRes = "passed";
    }
    // compares err code results
    if (strcmp($codeCheckRes, $xmlRes) == 0) {
        $overall = "passed";
        $passedTestCounter++;
    }

    // appends HTML table
    $overallTable = HtmlPrinter::addTableRow($overallTable, array($overall) , tableType::Overall, 1);

    $parserTable = HtmlPrinter::addTableRow($parserTable, array($expectedErr, $resCode, $codeCheckRes, $xmlRes) , tableType::Parser, 4);

    // removes or not testing files
    if ($noclean) {
        deleteFile($dirPath, $delta);
        deleteFile($dirPath, $outputXml);
    }
}

// interpret only file
function interpretTest($fileName, $dirPath, $expectedErr)
{
    global $interpretTable, $interpretPath, $passedTestCounter, $overallTable, $noclean;
    $codeCheckRes = "failed";
    $diffRes = "passed";
    $outputFile = "tmpOut.txt";
    $overall = "failed";

    // starts python script
    exec("python3.8 " . $interpretPath . " --source=\"" . $dirPath . $fileName . ".src" . "\" > " . $dirPath . $outputFile . " --input=\"" . $dirPath . $fileName . ".in\"", result_code: $resCode);

    // checks content and err codes
    // content is checked trough diff this time
    if ($expectedErr == $resCode) {
        if ($expectedErr == 0) {
            exec("diff " . $dirPath . $outputFile . " " . $dirPath . $fileName . ".out", result_code: $diffResCode);
            if ($diffResCode !== 0) {
                $diffRes = "failed";
            }
        }
        $codeCheckRes = "passed";
    }
    if (strcmp($codeCheckRes, $diffRes) == 0) {
        $overall = "passed";
        $passedTestCounter++;
    }
    // add new HTML table rows
    $overallTable = HtmlPrinter::addTableRow($overallTable, array($overall) , tableType::Overall, 1);

    $interpretTable = HtmlPrinter::addTableRow($interpretTable, array($expectedErr, $resCode, $codeCheckRes, $diffRes) , tableType::Interpret, 4);

    if ($noclean)
        deleteFile($dirPath, $outputFile);
}

// Combination of tests
// idea is the same as before but both of the tests are combined into one
function intParseTest($fileName, $dirPath, $expectedErr) {
    global $parserTable, $parserPath;
    global $interpretTable, $interpretPath, $passedTestCounter, $overallTable, $noclean;
    $parseCodeCheckRes = "failed";
    $intCodeCheckRes = "failed";
    $expectedParseErr = $expectedErr;
    $diffRes = "passed";
    $outputXml = "tmpOut.xml";
    $outputFile = "tmpOut.txt";
    $overall = "failed";

    exec("php8.1 " . $parserPath . " < " . $dirPath . $fileName . ".src" . " > " . $dirPath . $outputXml, result_code: $parsResCode);

    // parse part check
    if ($expectedErr == 21 || $expectedErr == 22 || $expectedErr == 23) {
        if ($parsResCode == $expectedErr) {
            $parseCodeCheckRes = "failed";
        }
    } else {
        $expectedParseErr = 0;
        $parseCodeCheckRes = "passed";
    }
    $parserTable = HtmlPrinter::addTableRow($parserTable, array($expectedParseErr, $parsResCode, $parseCodeCheckRes, $parseCodeCheckRes) , tableType::Parser, 4);

    exec("python3.8 " . $interpretPath . " --source=\"" . $dirPath . $outputXml . "\" > " . $dirPath . $outputFile . " --input=\"" . $dirPath . $fileName . ".in\"", result_code: $intResCode);

    if ($expectedErr == $intResCode) {
        if ($expectedErr == 0) {
            exec("diff " . $dirPath . $outputFile . " " . $dirPath . $fileName . ".out", result_code: $diffResCode);
            if ($diffResCode !== 0) {
                $diffRes = "failed";
            }
        }
        $intCodeCheckRes = "passed";
    }
    if ($intCodeCheckRes == "passed" && $diffRes == "passed" && $parseCodeCheckRes == "passed") {
        $overall = "passed";
        $passedTestCounter++;
    }

    $overallTable = HtmlPrinter::addTableRow($overallTable, array($overall) , tableType::Overall, 1);

    $interpretTable = HtmlPrinter::addTableRow($interpretTable, array($expectedErr, $intResCode, $intCodeCheckRes, $diffRes) , tableType::Interpret, 4);

    if ($noclean) {
        deleteFile($dirPath, $outputFile);
        deleteFile($dirPath, $outputXml);
    }
}

// helper function for file deletion
function deleteFile($dirPath, $file) {
    if (file_exists($ff = $dirPath . $file)) {
        unlink($ff);
    }
}

// start testing
function testRun() {
    // readOnly
    global $parserOnly, $interpretOnly, $fileIterator, $fileTable, $testCounter;

    //iterate trough files
    foreach ($fileIterator as $file) {
        if (strcmp($fileIterator->getExtension(), "src") == 0) {
            $fileNameWithoutEtension = basename($file->getFilename(), ".src");
            $currentDir = dirname($file) . "/";

            checkAndReplaceMissingFiles($fileNameWithoutEtension, $currentDir);
            $expectedErr = getExpectedErrorCode($fileNameWithoutEtension, $currentDir);
            $fileTable = HtmlPrinter::addTableRow($fileTable, array($file), tableType::File, 1);

            $testCounter++;

            // calls function based on type of test
            if (file_exists($file)) {
                if ($parserOnly) {
                    parserTest($fileNameWithoutEtension, $currentDir, $expectedErr);
                } else if ($interpretOnly) {
                    interpretTest($fileNameWithoutEtension, $currentDir, $expectedErr);
                } else {
                    intParseTest($fileNameWithoutEtension, $currentDir, $expectedErr);
                }
            }
        }
    }
}

// finishes HTML document and prints the final HTML to stdouts
function testTearDown() {
    global $parserOnly, $interpretOnly, $parserTable, $interpretTable, $fileTable, $passedTestCounter, $testCounter, $overallTable;

    if ($parserOnly)
        $parserTable = HtmlPrinter::completeTable($parserTable);
    if ($interpretOnly)
        $interpretTable = HtmlPrinter::completeTable($interpretTable);
    else {
        $interpretTable = HtmlPrinter::completeTable($interpretTable);
        $parserTable = HtmlPrinter::completeTable($parserTable);
    }

    $resultWindow = HtmlPrinter::setResultWindow($passedTestCounter, $testCounter);

    $fileTable = HtmlPrinter::completeTable($fileTable);
    $overallTable = HtmlPrinter::completeTable($overallTable);
    HtmlPrinter::finishHtmlFile($fileTable, $parserTable, $interpretTable, $overallTable, $resultWindow);
}
