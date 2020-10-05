import os
import re


def read_abbrevs(file):
    abbrevs = {'B': [], 'N': [], 'S': []}
    for line in open(os.path.join('data', file)):
        if not line.startswith('#'):
            abbrev, typ = line.strip().split('\t')[:2]
            abbrevs[typ].append(abbrev)
    return abbrevs

abbrevs = read_abbrevs('hr.abbrev')

LEFT_DANDA_RE = re.compile(r'^।+')
RIGHT_DANDA_RE = re.compile(r'।+$')

patterns = {
    'abbrev': r'|'.join(abbrevs['B']+abbrevs['N']+abbrevs['S']),
    'num': r'(?:(?<!\d)[+-])?\d+(?:[.,:/]\d+)*(?:[.](?!\.)|-[^\W\d_]+)?',
    'url': r'https?://[-\w/%]+(?:[.#?=&@;][-\w/%]+)+|\b\w+\.(?:\w+\.)?(?:com|org|net|gov|edu|int|io|eu|si|hr|rs|ba|me|mk|it|at|hu|bg|ro|al|de|ch|be|dk|se|no|es|pt|ie|fr|fi|cl|co|bo|br|gr|ru|uk|us|by|cz|sk|pl|lt|lv|lu|ca|in|tr|il|iq|ir|hk|cn|jp|au|nz)/?\b',
    'htmlesc': r'&#?[a-z0-9]+;',
    'tag': r'</?[a-z][\w:]*>|<[a-z][\w:]*/?>',
    'mail': r'[\w.-]+@\w+(?:[.-]\w+)+',
    'mention': r'@[a-z0-9_]+',
    'hashtag': r'#\w+(?:[.-]\w+)*',
    'emoticon': r'[=:;8][\'-]*(?:\)+|\(+|\]+|\[+|d\b|p\b|d+\b|p+\b|s+\b|o+\b|/|\\|\$|\*+)|-\.-|\^_\^|\([^\w\s]+\)|<3|</3|<\\3|\\o/',
    'word': r'(?:[*]{2,})?\w+(?:[@­\'-]\w+|[*]+\w+)*(?:[*]{2,})?',
    'arrow': r'<[-]+|[-]+>',
    'dot': r'[.!?/]{2,}',
    'space': r'\s+',
    'other': r'(.)\1*',
    'order': ('abbrev', 'num', 'url', 'htmlesc', 'tag', 'mail', 'mention', 'hashtag', 'emoticon', 'word', 'arrow', 'dot', 'space', 'other')
}

# transform abbreviation lists to sets for lookup during sentence splitting
for typ in abbrevs:
    abbrevs[typ] = set([e.replace('\\.', '.') for e in abbrevs[typ]])

spaces_re = re.compile(r'\s+', re.UNICODE)


def generate_tokenizer():
    token_re = re.compile(r'|'.join([patterns[e] for e in patterns['order']]), re.UNICODE | re.IGNORECASE)
    return token_re


def tokenize(tokenizer, paragraph):
    return [(e.group(0), e.start(0), e.end(0)) for e in tokenizer.finditer(paragraph.strip())]  # spaces_re.sub(' ',paragraph.strip()))]


def sentence_split(tokens):
    boundaries = [0]
    for index in range(len(tokens)-1):
        token = tokens[index][0]
        if token[0] in '.!?…।' or (token.endswith('.') and token.lower() not in abbrevs['N'] and len(token) > 2 and tokens[index+1][0][0] not in '.!?…।'):
            if tokens[index+1][0][0].isupper():
                boundaries.append(index+1)
                continue
            if index+2 < len(tokens):
                if tokens[index+2][0][0].isupper():
                    if tokens[index+1][0].isspace() or tokens[index+1][0][0] in '-»"\'':
                        boundaries.append(index+1)
                        continue
            if index+3 < len(tokens):
                if tokens[index+3][0][0].isupper():
                    if tokens[index+1][0].isspace() and tokens[index+2][0][0] in '-»"\'':
                        boundaries.append(index+1)
                        continue
            if index+4 < len(tokens):
                if tokens[index+4][0][0].isupper():
                    if tokens[index+1][0].isspace() and tokens[index+2][0][0] in '-»"\'' and tokens[index+3][0][0] in '-»"\'':
                        boundaries.append(index+1)
                        continue
        elif token[0] in ',:;':
            if index+2 < len(tokens):
                if tokens[index+2][0][0] in '-·•‐‑‒–—―⁃' and tokens[index+1][0].isspace():
                    boundaries.append(index+1)
                    continue
            if index+3 < len(tokens):
                if tokens[index+3][0] == ')' and (tokens[index+2][0].isnumeric() or len(tokens[index+2][0]) == 1):
                    boundaries.append(index+1)
                    continue
            if index+4 < len(tokens):
                if tokens[index+4][0] == ')' and tokens[index+1][0] == '।' and (tokens[index+3][0].isnumeric() or len(tokens[index+3][0]) == 1):
                    boundaries.append(index+1)
                    continue
    boundaries.append(len(tokens))
    raw_sents = []
    for index in range(len(boundaries)-1):
        raw_sents.append(tokens[boundaries[index]:boundaries[index+1]])

    sents = []
    correction = 0
    for raw_sent in raw_sents:
        sent = []
        for token in raw_sent:
            if token[0] == '।':
                correction += 1
                continue
            elif '।' in token[0]:
                token = (token[0], token[1]-correction, token[2]-correction)
                lft = LEFT_DANDA_RE.findall(token[0])
                if lft:
                    correction += len(lft[0])
                    token = (token[0].lstrip(lft[0]), token[1]-len(lft[0]), token[2]-len(lft[0]))
                rght = RIGHT_DANDA_RE.findall(token[0])
                if rght:
                    correction += len(rght[0])
                    token = (token[0].rstrip(rght[0]), token[1], token[2]-len(rght[0]))
                if token[0]:
                    sent.append(token)
            else:
                sent.append((token[0], token[1]-correction, token[2]-correction))
        if sent:
            sents.append(sent)
    return sents


def to_text(sent):
    text = ''
    for idx, (token, start, end) in enumerate(sent):
        if idx == 0 and token[0].isspace():
            continue
        text += token
    return text+'\n'


def represent(inpt, par_id, doc_id):
    output = ''
    if inpt:
        token_id = 0
        sent_id = 0
        output += '# newpar id = {}-p{}\n'.format(doc_id, par_id)
        for sent_idx, sent in enumerate(inpt):
            sent_id += 1
            token_id = 0
            output += '# sent_id = {}-p{}s{}\n'.format(doc_id, par_id, sent_id)
            output += '# text = {}'.format(to_text(sent))
            for token_idx, (token, start, end) in enumerate(sent):
                if not token[0].isspace():
                    token_id += 1
                    SpaceAfter = True
                    if len(sent) > token_idx+1:
                        SpaceAfter = sent[token_idx+1][0].isspace()
                    elif len(inpt) > sent_idx+1:
                        SpaceAfter = inpt[sent_idx+1][0][0].isspace()
                    if SpaceAfter:
                        output += str(token_id)+'\t'+token+'\t_'*8+'\tO'+'\t_'*3+'\n'
                    else:
                        output += str(token_id)+'\t'+token+'\t_'*7+'\tSpaceAfter=No\tO'+'\t_'*3+'\n'
            output += '\n'
    return output
