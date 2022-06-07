<?php

/**
* a helper class used for printing final HTML and
* do operations over it like adding new test files
**/

enum tableType
{
    case Parser;
    case Interpret;
    case File;
    case Overall;
}

class HtmlPrinter
{
    public static function printHeader() {
        $script = "$(document).ready(function(){
                    $('#test_table td.res').each(function(){
                        if ($(this).text() == 'passed') {
                            $(this).css('background-color','#8BF6C8');
                        } else {
                            $(this).css('background-color','#F1AFAF');
                        }
                    });
				  });";

        echo '<!DOCTYPE html>

        <html>
            <head>
                <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.js"></script>
                <script type="text/javascript">';

        echo $script;

        echo '</script>
        
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>IPP Test suite</title>
                <style>
                    table.innerTable {
                        border: 4px solid lightgray;
                        border-radius: 5px;
                    }
                    table {
                        border: 4px solid lightgray;
                        border-radius: 5px;
                    }
                    th{
                        background-color: #96D4D4;
                        border-radius: 5px;
                        text-align-last: center;
                    }
                    td{
                        background-color: #EEEBEB;
                        border-radius: 5px;
                        text-align-last: center;
                    }
                    h2 {
                        text-align-last: center;
                    }
                    td.resultWindow {
                        width: 10px;
                    }
                    div.resWindow {
                        width: 100px;
                        height: 100px;
                        text-align: center;
                        vertical-align: middle;
                        border: 5px solid lightgray;
                        margin: 5px; 
                        position:absolute;
                        top:0;
                        right:0;
                        background-color: #96D4D4;
			        }
                </style>
            </head> 
            
            <body style="background-color:white; font-family:verdana,serif;">';
    }

    // getting header part of HTML based on tested 
    public static function getFileTableHeader() {
        $header = '<div style="display: inline-block;">
			<h2>Tested files</h2>
			<table>
				<tr>
					<th>File Name</th>
				</tr>';
        return $header;
    }

    public static function getParserTableHeader() {
        $header = '
            <div style="display: inline-block;">
			<h2>Parser</h2>
			<table id="test_table">
				<tr>
					<th>Expected error</th>
					<th>Received error</th>
					<th>Error</th>
					<th>Output</th>
				</tr>';

        return $header;
    }

    public static function getInterpreterTableHeader() {
        $header = '
            <div  style="display: inline-block;">
			<h2>Interpreter</h2>
			<table id="test_table">
				<tr>
					<th>Expected error</th>
					<th>Received error</th>
					<th>Error</th>
					<th>Output</th>
				</tr>';

        return $header;
    }

    public static function getOverallTableHeader() {
        $header = '<div  style="display: inline-block;">
			<h2>Overall</h2>
			<table id="test_table">
				<col width="100px" />
				<tr>
					<th>Status</th>
				</tr>';

        return $header;
    }

    // finishes tables with closing elements
    public static function completeTable($table) {
        return $table . '</table>
                        </div>
                        ';
    }

    // adds new lines to tested table rows based on the type of test
    private static function createTdElements($tdArray, $typeOfTable, $numOfElements) {
        $finalElement = "";
       if (($typeOfTable == tableType::Parser || $typeOfTable == tableType::Interpret)  && $numOfElements == 4) {
           $finalElement = $finalElement . "<td>" . $tdArray[0] . "</td>\n";
           $finalElement = $finalElement . "<td>" . $tdArray[1] . "</td>\n";
           $finalElement = $finalElement . "<td class=\"res\">" . $tdArray[2] . "</td>\n";
           $finalElement = $finalElement . "<td class=\"res\">" . $tdArray[3] . "</td>\n";
       } else if ($typeOfTable == tableType::File && $numOfElements == 1) {
           $finalElement = $finalElement . "<td>" . $tdArray[0] . "</td>\n";
       } else if ($typeOfTable == tableType::Overall && $numOfElements == 1) {
           $finalElement = $finalElement . "<td class=\"res\">" . $tdArray[0] . "</td>\n";
       }else {
           exit(69);
       }

       return $finalElement;
    }

    // adds a new table row
    public static function addTableRow ($table, $tdArray, $typeOfTable, $numOfElements) {
        $table = $table . "\n<tr>";
        $rowContent = self::createTdElements($tdArray, $typeOfTable, $numOfElements);

        $table = $table . $rowContent . "</tr>";

        return  $table;
    }

    // ends the whole html document
    public static function finishHtmlFile ($fileTable, $parserTable, $interpretTable, $overalltable, $resultWindow) {
        if ($fileTable !== null)
            echo $fileTable;
        if ($parserTable !== null)
            echo $parserTable;
        if ($interpretTable !== null)
            echo $interpretTable;
        if ($overalltable !== null)
            echo $overalltable;
        if ($resultWindow !== null)
            echo $resultWindow;

        echo "</body></html>";
    }

    // sets the value of results of each test
    public static function setResultWindow($passed, $all) {
        $val = '<div class="resWindow"  style="display: inline-block;">
			        <h3>PASSED</h3>
			        <b style="font-size: small;">' . $passed . ' \\ ' . $all . '</b> </div>';

        return $val;
    }
}