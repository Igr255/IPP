<?php
declare(strict_types=1);
ini_set('display_errors', 'stderr');

/// IPP projekt 1 - IPPCODE22 parser
/// xhanus19 (Igor Hanus)

enum argType {
    case Var;
    case Symb;
    case Label;
    case Type;
    case None;
}

/// create XML header
$xml = new SimpleXMLElement('<?xml version="1.0" encoding="UTF-8"?>'
    .'<program language="IPPcode22">'.'</program>');

$instructionId = 1;

readArgs();

// feeding lines from STDIN
$firstLine = true;
while( $line = fgets( STDIN )) {
    preProcessLine($line, $xml);
}

/// prints the final XML at the end

if ($firstLine) {
    // in case an empty file is passed to stdin
    errorHandle(21);
} else {
    echo $xml->asXML();
}

function checkHeader($line) {
    if (strcmp($line, ".IPPcode22")!==0) {
        errorHandle(21);
    }
}

/// Help
function printHelp() {
    echo "\n";
    echo "PARSER FOR IPPCODE22:\n";
    echo "  Creates an output XML for interepreter base on the input\n";
    echo "  Example use: php8.1 parse.php < ippcode22.txt > outputXML.xml\n";
    echo "\n";
    exit(0);
}

/// reads input args
function readArgs() {
    global $argv;
    if (count($argv) > 1) {
        if ($argv[1] == "--help") {
            printHelp();
        }
    }
}

function preProcessLine($line, SimpleXMLElement $xml) {
    global $firstLine;

    // remove comments and newlines for further processing
    if (str_contains($line, "#"))
        $line = substr($line, 0, strpos($line, "#"));
    $line = rtrim($line, "\n ");
    $line = preg_replace('/\s+/', " ", $line);

    // ignore empty lines
    if ($line !== "") {
        // split line into array
        $lineArray = explode(" ", $line, PHP_INT_MAX);

        if ($firstLine) {
            $line = preg_replace('/\s+/', "", $line);
            checkHeader($line);
            $firstLine = false;
        } else {
            readOperation($lineArray, $xml);
        }
    }
}

function errorHandle(int $errNum) {
    switch ($errNum) {
        case 21:
            //fprintf(STDERR, "IPPcode22 header missing\n" );
            exit(21);
        case 22:
            //fprintf(STDERR, "Error in opCode\n" );
            exit(22);
        case 23:
            //fprintf(STDERR, "Other lex/synt error\n" );
            exit(23);
    }
}

function readOperation(array $OpArray, SimpleXMLElement $xml) {
    $operation = strtoupper($OpArray[0]);

    switch ($operation) {
        // no args
        case "CREATEFRAME":
        case "PUSHFRAME":
        case "POPFRAME":
        case "RETURN":
        case "BREAK":
            if (count($OpArray) == 1)
                setInstructionName($xml, $operation);
            else
                errorHandle(23);
            break;
        // <var>
        case "DEFVAR":
        case "POPS":
            processOperation($OpArray, $xml, $operation, 1, array(argType::Var));
            break;
        // <label>
        case "JUMP":
        case "LABEL":
        case "CALL":
            processOperation($OpArray, $xml, $operation, 1, array(argType::Label));
            break;
        // <symb>
        case "PUSHS":
        case "WRITE":
        case "EXIT":
        case "DPRINT":
            processOperation($OpArray, $xml, $operation, 1, array(argType::Symb));
            break;
        // <var> <type>
        case "READ":
            processOperation($OpArray, $xml, $operation, 2, array(argType::Var, argType::Type));
            break;
        // <var> <symb>
        case "MOVE":
        case "INT2CHAR":
        case "STRLEN":
        case "TYPE":
        case "NOT":
            processOperation($OpArray, $xml, $operation, 2, array(argType::Var, argType::Symb));
            break;
        // <label> <symb> <symb>
        case "JUMPIFEQ":
        case "JUMPIFNEQ":
            processOperation($OpArray, $xml, $operation, 3, array(argType::Label, argType::Symb, argType::Symb));
            break;
        // <var> <symb> <symb>
        case "ADD":
        case "SUB":
        case "MUL":
        case "IDIV":
        case "LT":
        case "GT":
        case "EQ":
        case "AND":
        case "OR":
        case "STRI2INT":
        case "CONCAT":
        case "GETCHAR":
        case "SETCHAR":
            processOperation($OpArray, $xml, $operation, 3, array(argType::Var, argType::Symb, argType::Symb));
            break;
        default:
            errorHandle(22);
            break;

    }
}

// create operation XML element
function setInstructionName(SimpleXMLElement $xml, $opName) {
    global $instructionId;

    $opElement = $xml->addChild("instruction");
    $opElement->addAttribute("order", (string)$instructionId);
    $opElement->addAttribute("opcode", $opName);

    $instructionId++;

    return $opElement;
}

// create var XML elements
function setInstructionArgs(SimpleXMLElement $xmlElement, $arg, argType $argType, int $argNum) {
    $typeString = "";
    if ($argType == argType::Var)
        $typeString = "var";
    else if ($argType == argType::Type)
        $typeString = "type";
    else if ($argType == argType::Label)
        $typeString = "label";
    else if ($argType == argType::Symb) {
        // do not split the symbol if it's a variable
        if (!matchPattern("/(GF|LF|TF)@/", $arg)) {
            $symbolSplit = explode("@", $arg);
            $typeString = $symbolSplit[0];
            $arg = $symbolSplit[1];
            checkConstant($arg, $typeString);
        } else {
            $typeString = "var";
        }
    }

    $argElement =  $xmlElement->addChild(sprintf("arg%d", $argNum));
    $argElement->addAttribute("type", $typeString);
    $argElement[0] = $arg;
}

/// processes arguments of a given operation and sends them to be evaluated using regex
function processOperation($opArray, SimpleXMLElement $xml, $opName, $numOfArgs, $argTypes) {
    $parentElement = setInstructionName($xml, $opName);

    $argNumCheck = count($opArray, $mode = COUNT_NORMAL) - 1;
    if ($numOfArgs > 0) {
        if ($argNumCheck !== $numOfArgs) {
            errorHandle(23);
        } else {
            if ($numOfArgs == 2) {
                if (checkType($argTypes[0], $opArray[1]) && checkType($argTypes[1], $opArray[2])) {
                    setInstructionArgs($parentElement, $opArray[1], $argTypes[0], 1);
                    setInstructionArgs($parentElement, $opArray[2], $argTypes[1], 2);
                }
            } else if ($numOfArgs == 3) {
                if (checkType($argTypes[0], $opArray[1]) && checkType($argTypes[1], $opArray[2]) && checkType($argTypes[2], $opArray[3])) {
                    setInstructionArgs($parentElement, $opArray[1], $argTypes[0], 1);
                    setInstructionArgs($parentElement, $opArray[2], $argTypes[1], 2);
                    setInstructionArgs($parentElement, $opArray[3], $argTypes[2], 3);
                }
            } else if ($numOfArgs == 1) {
                if (checkType($argTypes[0], $opArray[1])) {
                    setInstructionArgs($parentElement, $opArray[1], $argTypes[0], 1);
                }
            }
        }
    }
}

/// Checks if input OP argument is correct
function checkType($argType, $arg) {
    $errHandle = true; // true -> no err

    if ($argType == argType::Type) {
        $errHandle = matchPattern("/^(int|bool|string|nil)$/", $arg);
    } else if ($argType == argType::Var) {
        $errHandle = matchPattern("/((GF|LF|TF)@([A-Za-z_$&\-%!*?])([A-Za-z0-9_$\-&%!*?])*)$/i", $arg);
    } else if ($argType == argType::Symb) {
        if(!matchPattern("/((GF|LF|TF)@([A-Za-z_$-&%!*?])([A-Za-z0-9_$-&%!*?])*)$/i", $arg)) {
            $errHandle = matchPattern("/^(int|bool|string|nil)@(\\\[0-9]{3}|[a-zA-Z0-9!]|\\\[sntr\"']|[$-&]|[(-\/]|[:-@]|\[|[]-`]|[{-~]|[\x{80}-\x{FFFF}])*$/iu", $arg);
        }
    } else if ($argType == argType::Label) {
        $errHandle = matchPattern("/^(?![0-9])((?!@)([A-Za-z0-9_$\-&%!*?]))*$/", $arg);
    }

    if (!$errHandle)
        errorHandle(23);


    return true;
}

/// helper function to handle regex parsing
function matchPattern(string $pattern, string $subject) {
    if (preg_match($pattern, $subject) == 1) {
        return true;
    } else {
        return false;
    }
}

/// checks if "Const" is int he correct format
function checkConstant($argValue, $typeString) {
    $errHandle = true; // true -> no err

    switch ($typeString) {
        case "int":
            $errHandle = is_numeric($argValue);
            break;
        case "string":
            break;
        case "nil":
            if (strcmp($argValue, "nil")!==0)
                $errHandle = false;
            break;
        case "bool":
            if (strcmp($argValue, "true")!==0 && strcmp($argValue, "false")!==0)
                $errHandle = false;
            break;
        default:
            errorHandle(23);
    }

    if (!$errHandle)
        errorHandle(23);
}
