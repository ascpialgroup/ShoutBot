import re
import html
import bbcode
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML


class Parser:
	def __init__(self, config):
		self.config = config
		self.init_bbcode2markdown()
		self.markdown = MarkdownIt(
			{
				'options': {
					'maxNesting': 20,
					'html': False,
					'linkify': False,
					'typographer': False,
					'quotes': '“”‘’',
					'xhtmlOut': False,
					'breaks': False,
					'langPrefix': 'language-',
					'highlight': None
				},
				'components': {
					'core': { 'rules': ['normalize', 'block', 'inline', 'linkify', 'replacements', 'smartquotes'] },
					'block': { 'rules':  ['code', 'fence', 'blockquote', 'paragraph'] },
					'inline': { 'rules': ['text', 'newline', 'escape', 'backticks', 'strikethrough', 'emphasis', 'entity'] }
				}
			}, renderer_cls=RendererBBCODE)

	def init_bbcode2markdown(self):
		def render_quote(tag_name, value, options, parent, context):
			author = u''
			if 'quote' in options:
				author = options['quote']

			# for some reason \n are replaced with \r when landing here
			value = value.replace('\r', '\n')

			nl = '\n' # can't be used in fstrings
			return f"\n{nl.join([f'> {line}' for line in value.split(nl)])}\n— {author}\n"

		def render_url(tag_name, value, options, parent, context):
			url = u''
			if 'url' in options:
				url = options['url']
			return f'[{value}]({url})'

		self.bbcode2markdown = bbcode.Parser(install_defaults=False, escape_html=False)
		self.bbcode2markdown.add_simple_formatter('ispoiler', '|| %(value)s ||')
		self.bbcode2markdown.add_simple_formatter('color', '%(value)s')
		self.bbcode2markdown.add_simple_formatter('img', '%(value)s')
		self.bbcode2markdown.add_simple_formatter('b', '**%(value)s**')
		self.bbcode2markdown.add_simple_formatter('u', '__%(value)s__')
		self.bbcode2markdown.add_simple_formatter('s', '~~%(value)s~~')
		self.bbcode2markdown.add_simple_formatter('i', '*%(value)s*')
		self.bbcode2markdown.add_formatter('quote', render_quote, strip=True, swallow_trailing_newline=True)
		self.bbcode2markdown.add_formatter('url', render_url, strip=True, swallow_trailing_newline=True)

	def parse_bbcode2markdown(self, msg):
		# shortcut completions and other quick changes
		msg = msg.replace('[url=/forum', '[url=https://www.tiplanet.org/forum')
		msg = msg.replace('[img]/forum', '[img]https://www.tiplanet.org/forum')
		msg = re.sub(r'\[url=(.*)]\[img](.*)\[\/img]\[\/url]', r'\g<1>', msg)

		# bbcode and html escaping
		msg = html.unescape(html.unescape(self.bbcode2markdown.format(msg)))
		msg = re.sub(r'< *br *\/? *>', r'\n', msg)

		# simple urls are transformed to a weird bugged <a>
		def repl_func(s):
			s = s.group(1)
			s = s[0:int(len(s)/2)]
			s = s[0:s.rfind('%')]
			return s
		msg = re.sub(r'<a rel="nofollow" href="(.*)<\/a>', repl_func, msg)

		# emojis
		for tp_name, ds_name in self.config["emojis"].items():
			msg = msg.replace(f':{tp_name}:', f'<:{ds_name}>')

		return msg.strip()

	def parse_markdown2bbcode(self, msg):
		# fix emojis
		msg = re.sub(r'<(:\S+:)\S+>', r'\g<1>', msg)
		return self.markdown.render(msg)


class RendererBBCODE(RendererHTML):
	def paragraph_open(self, tokens, idx, options, env):
		return ''

	def paragraph_close(self, tokens, idx, options, env):
		return ''

	def em_open(self, tokens, idx, options, env):
		return '[i]'

	def em_close(self, tokens, idx, options, env):
		return '[/i]'

	def s_open(self, tokens, idx, options, env):
		return'[s]'

	def s_close(self, tokens, idx, options, env):
		return'[/s]'

	def strong_open(self, tokens, idx, options, env):
		if tokens[idx].markup == "__":
			return '[u]'
		else:
			return'[b]'

	def strong_close(self, tokens, idx, options, env):
		if tokens[idx].markup == "__":
			return '[/u]'
		else:
			return'[/b]'

	def code_inline(self, tokens, idx, options, env):
		token = tokens[idx]
		return (
			f"[code]{tokens[idx].content}[/code]"
		)

	def code_block(self, tokens, idx, options, env):
		return (
			f"[code]{tokens[idx].content}[/code]\n"
		)

	def fence(self, tokens, idx, options, env):
		return (
			f"[code]{tokens[idx].content}[/code]\n"
		)

	def blockquote_open(self, tokens, idx, options, env):
		return "[quote]"

	def blockquote_close(self, tokens, idx, options, env):
		return "[/quote]"