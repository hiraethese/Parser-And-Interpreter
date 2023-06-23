<?php

// Baturov Illia (xbatur00), student 2. ročníku FIT VUT v Brně
// IPP projekt - 1. úloha v PHP 8.1

// výstup do STDERR
ini_set('display_errors', 'stderr');

// argumenty skriptu (--help)
if ($argc > 2)
{
    exit(10);
}
else if ($argc == 2)
{
    if ($argv[1] == "--help")
    {
        echo("--- Napoveda skriptu ---\n");
        echo("Skript typu filtr (parse.php) nacte ze standartniho vstupu zdrojovy kod v IPPcode23, ");
        echo("zkontrolue lexikalni a syntaktickou spravnost kodu a vypise na standartni vystup XML reprezentaci programu.\n");
        echo("\nPouziti skriptu:\n");
        echo("parse.php [--help] < INPUTFILE\n");
        echo("\nChybove navratove kody:\n");
        echo("21 - chybna nebo chybejici hlavicka;\n");
        echo("22 - neznamy nebo chybny operacni kod;\n");
        echo("23 - jina lexikalni nebo syntakticka chyba.\n");
        exit(0);
    }
    else
    {
        exit(10);
    }
}

// test hlavičky
$ipp_header = false;
// pořadí instrukce
$instruction_order = 0;
// hodnota argumentu
$argument_value = "NO_VALUE";
// typ instrukce
$instruction_type = "NO_TYPE";
// regex nil
$reg_nil = "\A(nil@nil)\z";
// regex integer
$reg_int = "\A(int)@[+-]?[0-9]+\z";
// regex type
$reg_type = "\A(int|string|bool)\z";
// regex boolean
$reg_bool = "\A(bool)@(false|true)\z";
// regex string
$reg_string = "\A(string)@([^\s#\\\\]|\\\\[0-9]{3})*\z";
// regex label
$reg_label = "\A[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*\z";
// regex variable
$reg_var = "\A(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*\z";

// detektor typu (pro symbol)
function type_detector_symbol($string)
{
    // globalizace
    global $instruction_type, $argument_value;
    global $reg_var, $reg_int, $reg_bool, $reg_string, $reg_nil;
    // var
    if( preg_match( "/$reg_var/", $string ) )
    {
        $instruction_type = "var";
        $argument_value = $string;
        replace_special_characters($argument_value);
        return;
    }
    // int
    else if( preg_match( "/$reg_int/", $string ) )
    {
        $instruction_type = "int";
        value_detector_symbol($string);
        return;
    }
    // bool
    else if( preg_match( "/$reg_bool/", $string ) )
    {
        $instruction_type = "bool";
        value_detector_symbol($string);
        return;
    }
    // string
    else if( preg_match( "/$reg_string/", $string ) )
    {
        $instruction_type = "string";
        value_detector_symbol($string);
        replace_special_characters($argument_value);
        return;
    }
    // nil
    else if( preg_match( "/$reg_nil/", $string ) )
    {
        $instruction_type = "nil";
        value_detector_symbol($string);
        return;
    }
    else
    {
        exit(23);
    }
}

// detektor hodnoty symbolu
function value_detector_symbol($string)
{
    global $argument_value;
    if ( preg_match( "/(?<=@).*\z/", $string, $group ) ) {
        $argument_value = $group[0];
    }
    return;
}

// nahradit speciální znaky <, > a & (pro string a variable)
function replace_special_characters($string)
{
    global $argument_value;
    $patterns = array("/&/", "/</", "/>/");
    $replacements = array("&amp;", "&lt;", "&gt;");
    $argument_value = preg_replace($patterns, $replacements, $string);
    return;
}

// detektor typu (pro variable)
function type_detector_variable($string)
{
    // globalizace
    global $instruction_type, $argument_value;
    global $reg_var;
    // var
    if( preg_match( "/$reg_var/", $string ) )
    {
        $instruction_type = "var";
        $argument_value = $string;
        replace_special_characters($argument_value);
        return;
    }
    else
    {
        exit(23);
    }
}

// detektor typu (pro label)
function type_detector_label($string)
{
    // globalization
    global $instruction_type, $argument_value;
    global $reg_label;
    // var
    if( preg_match( "/$reg_label/", $string ) )
    {
        $instruction_type = "label";
        $argument_value = $string;
        return;
    }
    else
    {
        exit(23);
    }
}

// detektor typu (for type)
function type_detector_type($string)
{
    // globalization
    global $instruction_type, $argument_value;
    global $reg_type;
    // var
    if( preg_match( "/$reg_type/", $string ) )
    {
        $instruction_type = "type";
        $argument_value = $string;
        return;
    }
    else
    {
        exit(23);
    }
}

// generátor - generuje řádek jako proměnnou line
function stdin_stream()
{
    while ( $line = fgets(STDIN) )
    {
        yield $line;
    }
}

// čtení každého řádku ze STDIN
foreach ( stdin_stream() as $line )
{
    // explode_comments - rozdělení komentářů (trim pro odstranění nových řádků)
    $explode_comments = explode("#", trim($line, "\n"), 2);

    // test hlavičky - pokud je false, bude to mít za následek chybu
    if( $ipp_header == false )
    {
        // řádek hlavičky (může být s komentářem)
        if ( preg_match( "/^\s*(.IPPcode23)\s*(#.*|\s*)$/i", $line ) )
        {
            $ipp_header = true;
            echo("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
            echo("<program language=\"IPPcode23\">\n");
            continue;
        }
        // prázdné řádky a řádky komentářů
        else if ( preg_match( "/^\s*(#.*|\s*)$/", $line ) )
        {
            continue;
        }
        // žádná hlavička
        else
        {
            exit(21);
        }
    }

    // explode_instructions - rozdělení instrukce (array_filter pro odstranění prázdných prvků pole)
    $explode_instructions = array_filter( preg_split("/\s+/", trim($explode_comments[0], "\n")) );

    // pokud existuje
    if ( isset($explode_instructions[0]) )
    {

        // instrukce velkými písmeny
        $operation_code = strtoupper( $explode_instructions[0] );

        // switch case
        switch ( $operation_code )
        {
            // CREATEFRAME
            case 'CREATEFRAME':
            // PUSHFRAME
            case 'PUSHFRAME':
            // POPFRAME
            case 'POPFRAME':
            // RETURN
            case 'RETURN':
            // BREAK
            case 'BREAK':
                if ( !isset($explode_instructions[1]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\"/>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // DEFVAR <var>
            case 'DEFVAR':
            // POPS <var>
            case 'POPS':
                if ( isset($explode_instructions[1]) && !isset($explode_instructions[2]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_variable($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // PUSHS <symb>
            case 'PUSHS':
            // WRITE <symb>
            case 'WRITE':
            // EXIT <symb>
            case 'EXIT':
            // DPRINT <symb>
            case 'DPRINT':
                if ( isset($explode_instructions[1]) && !isset($explode_instructions[2]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_symbol($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // CALL <label>
            case 'CALL':
            // LABEL <label>
            case 'LABEL':
            // JUMP <label>
            case 'JUMP':
                if ( isset($explode_instructions[1]) && !isset($explode_instructions[2]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_label($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // MOVE <var> <symb>
            case 'MOVE':
            // NOT <var> <symb>
            case 'NOT':
            // INT2CHAR <var> <symb>
            case 'INT2CHAR':
            // STRLEN <var> <symb>
            case 'STRLEN':
            // TYPE <var> <symb>
            case 'TYPE':
                if ( isset($explode_instructions[1]) && isset($explode_instructions[2]) && !isset($explode_instructions[3]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_variable($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    type_detector_symbol($explode_instructions[2]);
                    echo("\t\t<arg2 type=\"$instruction_type\">$argument_value</arg2>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // READ <var> <type>
            case 'READ':
                if ( isset($explode_instructions[1]) && isset($explode_instructions[2]) && !isset($explode_instructions[3]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_variable($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    type_detector_type($explode_instructions[2]);
                    echo("\t\t<arg2 type=\"$instruction_type\">$argument_value</arg2>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // ADD <var> <symb1> <symb2>
            case 'ADD':
            // SUB <var> <symb1> <symb2>
            case 'SUB':
            // MUL <var> <symb1> <symb2>
            case 'MUL':
            // IDIV var> <symb1> <symb2>
            case 'IDIV':
            // LT <var> <symb1> <symb2>
            case 'LT':
            // GT <var> <symb1> <symb2>
            case 'GT':
            // EQ <var> <symb1> <symb2>
            case 'EQ':
            // AND <var> <symb1> <symb2>
            case 'AND':
            // OR <var> <symb1> <symb2>
            case 'OR':
            // STRI2INT <var> <symb1> <symb2>
            case 'STRI2INT':
            // CONCAT <var> <symb1> <symb2>
            case 'CONCAT':
            // GETCHAR <var> <symb1> <symb2>
            case 'GETCHAR':
            // SETCHAR <var> <symb1> <symb2>
            case 'SETCHAR':
                if ( isset($explode_instructions[1]) && isset($explode_instructions[2]) && isset($explode_instructions[3]) && !isset($explode_instructions[4]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_variable($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    type_detector_symbol($explode_instructions[2]);
                    echo("\t\t<arg2 type=\"$instruction_type\">$argument_value</arg2>\n");
                    type_detector_symbol($explode_instructions[3]);
                    echo("\t\t<arg3 type=\"$instruction_type\">$argument_value</arg3>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // JUMPIFEQ <label> <symb1> <symb2>
            case 'JUMPIFEQ':
            // JUMPIFNEQ <label> <symb1> <symb2>
            case 'JUMPIFNEQ':
                if ( isset($explode_instructions[1]) && isset($explode_instructions[2]) && isset($explode_instructions[3]) && !isset($explode_instructions[4]) )
                {
                    $instruction_order++;
                    echo("\t<instruction order=\"$instruction_order\" opcode=\"$operation_code\">\n");
                    type_detector_label($explode_instructions[1]);
                    echo("\t\t<arg1 type=\"$instruction_type\">$argument_value</arg1>\n");
                    type_detector_symbol($explode_instructions[2]);
                    echo("\t\t<arg2 type=\"$instruction_type\">$argument_value</arg2>\n");
                    type_detector_symbol($explode_instructions[3]);
                    echo("\t\t<arg3 type=\"$instruction_type\">$argument_value</arg3>\n");
                    echo("\t</instruction>\n");
                    break;
                }
                else
                {
                    exit(23);
                }
            // ostatní
            default:
                exit(22);
        }
    }
    else
    {
        continue;
    }
}

// konec programu
echo("</program>\n");
exit(0);

?>
