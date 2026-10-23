"""Optional site configuration, defaults and matching editor-schema properties."""
import copy
from data_validation import ASSET_PATTERN, fail, integer, object_value, string

DEFAULTS = {
    'theme': {'background': '#e7eeed', 'ink': '#315f69', 'accent': '#7295a7',
              'paper': '#f4f3ef', 'envelope': '#cbd6dc'},
    'assets': {'background': 'assets/demo/sea.png', 'motif': 'assets/demo/botanical.svg',
               'texture': 'assets/demo/paper.png', 'motifAlt': '青绿色枝叶图案'},
    'sections': {'dates': True, 'collage': True, 'quiz': True},
    'behavior': {'persistProgress': True, 'liveAutoplay': True, 'backgroundPreload': True,
                 'openingMotion': 'auto', 'hintAfterAttempts': 2},
    'labels': {
        'pageSuffix': '生日邀请函', 'headerRight': 'WITH LOVE, ALWAYS',
        'envelopeTop': 'Happy', 'envelopeBottom': 'birthday',
        'letterLeftTop': 'A SEAT', 'letterLeftBottom': 'IN OUR',
        'letterRightTop': 'SUMMER', 'letterRightBottom': 'STORY',
        'birthdayLabel': '生日', 'invitationLabel': '邀请函', 'invitationEnglish': 'INVITATION',
        'openingLoading': '海风捎来了一封信', 'openingReady': '轻触信封，打开这份生日邀请',
        'openingOpened': '生日邀请函已展开', 'enterButton': '走进这一年', 'replayButton': '重读这封信',
        'navDates': '日期照片', 'navCollage': '拼贴照片', 'navQuiz': '趣味问答',
        'datesEyebrow': 'Remember the day?', 'datesTitle': '把日子拼起来，\n让回忆显影。',
        'datesDescription': '选取四个数字组成正确日期即可解锁当日回忆',
        'welcomeButton': '带我看一段回忆', 'unlockedLabel': '段回忆已解锁',
        'datesSummary': '{dateCount}个日期，{photoCount}个瞬间，等你逐一开启。',
        'hintButton': '给我提示', 'unlockButton': '解锁这一天',
        'dateSelected': '选好日期后，试着解锁这一天。',
        'dateInvalid': '这个日期好像不成立，检查一下月份和天数吧。',
        'dateMissing': '这一天还没有照片，再想一个日子吧。',
        'dateUnlocked': '日期猜对了！这一天的照片，已经为你打开。',
        'dateWelcome': '先从这段回忆开始。其他日子，等你逐个解锁。',
        'dateReset': '重新选一个，值得被记住的日子。',
        'dateAllUnlocked': '所有日期都已解锁，点开下面的相册，再看一遍吧。',
        'dateCalendarLead': '按 {year} 年的日历想一想：',
        'collageEyebrow': 'Pieces of you', 'collageTitle': '关于你的，\n每一小片。',
        'collageDescription': '把喜欢的瞬间，\n拼成一张独一无二的你。',
        'collageHelp': '左右滑动，或点击左右键翻看。\n轻触照片，放大看细节。',
        'overviewOpen': '查看全部 {count} 张', 'overviewClose': '收起拼贴总览',
        'overviewNote': '按原有编号排列，轻触任意一张放大查看。',
        'progressSaved': '浏览进度保存在当前浏览器', 'progressSession': '浏览进度仅在本次访问中保留',
        'progressUnavailable': '当前浏览器暂无法保存进度，本次浏览不受影响',
        'quizEyebrow': 'How well do you remember?', 'quizTitle': '这道题，\n你一定知道。',
        'quizLabel': '默契小测验', 'quizWelcome': '关于{recipient}，你了解多少？',
        'quizSummary': '共 {count} 道题，来试试我们的默契。', 'quizStart': '开始答题',
        'quizNext': '下一题', 'quizSkip': '跳过，下一题', 'quizResultButton': '看看结果',
        'quizRetry': '再玩一次', 'quizCorrect': '答对啦！',
        'quizWrong': '这次的答案是 {answer}。', 'quizPendingAnswer': '你选择了 {answer}，答案待揭晓。',
        'quizPendingImages': '头像图片待补充，这题先跳过。',
        'quizScore': '答对了 {score} / {total} 题', 'quizComplete': '本轮问答已完成',
        'quizPartial': '图片或答案待补充的题目暂不计分。',
        'quizThanks': '谢谢你，陪我把这些瞬间再记了一遍。生日快乐，{recipient}！',
        'quizSavedSummary': '已保留这台设备上的答题进度。',
        'quizSavedResult': '查看上次结果', 'quizContinue': '继续上次答题',
        'footerMessage': 'Happy birthday.', 'backToLetter': '回到这封信'
    }
}

TOKENS = {
    'overviewOpen': ('count',),
    'datesSummary': ('dateCount', 'photoCount'), 'dateCalendarLead': ('year',),
    'quizWelcome': ('recipient',), 'quizSummary': ('count',), 'quizWrong': ('answer',),
    'quizPendingAnswer': ('answer',), 'quizScore': ('score', 'total'), 'quizThanks': ('recipient',)
}


def schema_properties():
    result = {}
    for group, values in DEFAULTS.items():
        properties = {}
        for key, value in values.items():
            field = {'default': value}
            if isinstance(value, bool):
                field['type'] = 'boolean'
            elif group == 'theme':
                field.update(type='string', pattern=r'^#[0-9a-fA-F]{6}(?![\s\S])')
            elif group == 'assets' and key != 'motifAlt':
                field.update(type='string', pattern=ASSET_PATTERN.removesuffix('$')+r'(?![\s\S])')
            elif key == 'hintAfterAttempts':
                field.update(type='integer', minimum=0, maximum=10)
            elif key == 'openingMotion':
                field.update(type='string', enum=['auto', 'reduced'])
            else:
                field.update(type='string', maxLength=500)
                if group == 'labels':
                    tokens = TOKENS.get(key, ())
                    # Literal braces are reserved; only this label's tokens are accepted.
                    token_pattern = '|'.join(tokens)
                    atom = r'[^{}]' + (r'|\{(?:'+token_pattern+r')\}' if tokens else '')
                    field['pattern'] = r'^(?:'+atom+r')*(?![\s\S])'
                    field['description'] = 'Plain text. Tokens: '+(', '.join('{'+t+'}' for t in tokens) or 'none')
            properties[key] = field
        result[group] = {'type': 'object', 'additionalProperties': False, 'properties': properties,
                         'description': 'Optional overrides; omitted fields use the documented defaults.'}
    return result


def validate_options(site):
    for group, schema in schema_properties().items():
        if group not in site:
            continue
        values = site[group]; path = 'site.'+group
        object_value(values, path)
        for key, value in values.items():
            if key not in schema['properties']:
                fail(path+'.'+key, 'unknown configuration field')
            rule = schema['properties'][key]; field = path+'.'+key
            if rule['type'] == 'boolean':
                if type(value) is not bool:
                    fail(field, 'expected a boolean')
            elif rule['type'] == 'integer':
                integer(value, field, rule['minimum'], rule['maximum'])
            else:
                string(value, field, rule.get('maxLength'), pattern=rule.get('pattern'))
                if 'enum' in rule and value not in rule['enum']:
                    fail(field, 'expected auto or reduced')


def resolve_options(site):
    validate_options(site)
    options = copy.deepcopy(DEFAULTS)
    for group in options:
        options[group].update(site.get(group, {}))
    return options
