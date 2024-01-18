import ply.lex as lex

tokens = (
	'DECLARE',
	'BEGIN',
	'COMMA',
	'END',
	'SEMICOLON',
	'NUM',
	'PLU',
	'MIN',
	'MUL',
	'DIV',
	'MOD',
	'EQ',
	'NEQ',
	'LEQ',
	'GEQ',
	'LT',
	'GT',
	'ASSIGN',
	'L',
	'R',
	'COLON',
	'IF',
	'THEN',
	'ELSE',
	'ENDIF',
	'DO',
	'FOR',
	'FROM',
	'TO',
	'DOWNTO',
	'ENDFOR',
	'WHILE',
	'ENDWHILE',
	'REPEAT',
	'UNTIL',
	'READ',
	'WRITE',
	'PIDENTIFIER'
)

def t_COMMENT(t):
	r'\[[^\]]*\]'
	x = t.value.count("\n")
	t.lexer.lineno += x
	pass

def t_newline(t):
	r'\r?\n{1}'
	t.lexer.lineno += 1

def t_NUM(t):
	r'\d+'
	t.value = int(t.value)	
	return t

t_PIDENTIFIER = r'[_a-z]+'

t_DECLARE	= r'DECLARE'
t_COMMA		= r','
t_BEGIN		= r'BEGIN'
t_END		= r'END'
t_SEMICOLON	= r';'

t_L	= r'\('
t_R	= r'\)'
t_COLON	= r':'

t_PLU	= r'\+'
t_MIN	= r'\-'
t_MUL	= r'\*'
t_DIV	= r'\/'
t_MOD	= r'\%'

t_EQ	= r'='
t_NEQ	= r'!='
t_LEQ	= r'<='
t_GEQ	= r'>='
t_LT	= r'<'
t_GT	= r'>'

t_ASSIGN = r':='

t_IF	= r'IF'
t_THEN	= r'THEN'
t_ELSE	= r'ELSE'
t_ENDIF	= r'ENDIF'

t_DO		= r'DO'
t_FOR		= r'FOR'
t_FROM		= r'FROM'
t_TO		= r'TO'
t_DOWNTO	= r'DOWNTO'
t_ENDFOR	= r'ENDFOR'
t_WHILE		= r'WHILE'
t_ENDWHILE	= r'ENDWHILE'
t_REPEAT	= r'REPEAT'
t_UNTIL		= r'UNTIL'
t_READ		= r'READ'
t_WRITE		= r'WRITE'

t_ignore  = ' \t'

def t_error(t):
	print("Zly znak '%s'" % t.value[0])
	t.lexer.skip(1)

lexer = lex.lex()
