/**
 * 简体中文 (中文)
 *
 * 结构与 ko.js / en.js 相同。en.js 是翻译参照。
 * 下半部分 (channels / checklists / mock) 是覆盖数据文件中韩文原文的译文。
 * 快捷提问按钮的 text 会原样发送给后端，后端根据提问文字自动识别语言，
 * 所以这里的 text 必须是自然的中文提问。
 */
export default {
  meta: { code: 'zh', name: '中文', nativeName: '中文', tag: 'zh-CN' },

  common: {
    ragActive: 'RAG 已启用',
    yes: '是',
    no: '否',
    close: '关闭',
    cancel: '取消',
    example: '示例',
    gradeN: '{n}年级',
    thinking: '…',
  },

  nav: { home: '首页', chat: '聊天', calendar: '日历', history: '记录', profile: '我的' },

  splash: { tagline: '为您的韩国留学生活提供指引' },

  toast: {
    notifSoon: '正在前往通知页面',
    allStepsDone: '🎉 您已完成所有步骤！',
    schoolDone: '🎉 选课准备已全部完成！',
    arcDone: '🎉 补办准备已全部完成！',
    filterApplied: '已应用“{name}”筛选',
    relatedLoading: '正在加载相关问题',
    calendarLinked: '📅 已添加到日历！',
  },

  tags: {
    d2: '#D-2', extend: '#延期', docs: '#材料', immigration: '#出入境', period: '#期限',
  },

  time: { today: '今天', justNow: '刚刚', daysAgo: '{n}天前', weeksAgo: '{n}周前' },

  home: {
    notifSoon: '通知功能即将上线',
    greeting: '您好，{name}！',
    greetingFallback: '欢迎',
    urgentLabel: '🚨 需要立即确认',
    urgentTitle: '签证即将到期',
    urgentPreview: 'D-87 — 请立即准备延期材料',
    itemIsExample: '此项为示例',
    myChannels: '📂 我的频道',
    tapToOpen: '点击进入频道',
    emptyTitle: '还没有创建的频道',
    emptyDesc: '在主聊天中选择您感兴趣的领域，\n就会创建对应的频道。',
    startInMain: '💬 从主聊天开始',
    belowAreExamples: '以下为示例',
    channelIsExample: '此频道为示例',
    newChannel: '创建新频道',
    newChannelSub: '在主聊天中选择领域',
    ghost: {
      visa: '签证延期、居留期限、外国人登录相关问题',
      school: '选课、校历、宿舍、奖学金',
      job: '兼职就业许可、实习、打工规定',
      house: '租房合同、管理费、搬家注意事项',
      insurance: '健康保险参保、就医、保险福利',
    },
  },

  chat: {
    subtitle: '向所有频道提问',
    cat: {
      visa: 'ARC 重新登记 · 材料 · 申请流程',
      job: '许可流程 · 所需材料 · 注意事项',
      school: '选课 · 校历 · 改选期限',
      house: '租房 · 迁入申报 · 合同注意事项',
    },
    welcomeTitle: '您想了解什么呢？',
    welcomeDesc: '签证、学校、住房、打工等，\n选择您关心的主题即可立即开始。',
    welcomeBtn: '💬 前往主聊天',
    createdSection: '✅ 刚创建的频道',
    createdPreview: '在专属频道获得更详细的解答',
    viewInChannel: '频道 — 查看详情',
    channelCreated: '“{name}”频道已创建 🎉',
    createTitle: '要创建“{name}”频道吗？',
    createDesc: '您将获得更详细、\n更专业的解答。',
    createBtn: '创建频道',
    later: '以后再说',
    error: '加载回复时出现问题，请稍后重试。',
  },

  channel: {
    chatTab: '💬 聊天',
    knowledgeTab: '📚 知识卡片',
    searchInChannel: '搜索本频道对话...',
    checklist: '📋 清单',
  },

  visa: {
    expires: '🗓 {type} 到期日',
    alarmOn: '🔔 已开启提醒',
    backToChannel: '签证频道',
  },

  calendar: {
    title: '日历',
    today: '今天',
    emptyTitle: '暂无日程',
    emptySub: '在聊天中创建清单，\n并添加到日历吧',
    fromChat: '这是通过聊天添加的日程',
    chatBadge: '💬 聊天',
    done: '已完成',
  },

  guide: {
    progress: '已完成 {done} / {total} 步',
    groupProgress: '已完成 {done}/{total}',
    docsPrep: '📁 准备材料',
    apply: '📋 申请',
    regPrep: '📅 注册准备',
    courseReg: '📋 选课',
    autoSave: '✅ 勾选状态会自动保存，关闭应用后也会保留。',
    visaTitle: 'D-2 签证延期流程',
    arcTitle: '外国人登录证补办流程',
    schoolTitle: '选课与注册准备',
    officeBasis: '以前往出入境管理事务所办理为准',
    schoolBasis: '以学校门户网站为准 · 请在开学前确认',
    schoolChannel: '校园生活频道',
    moreNotes: '⚠️ 查看更多注意事项',
    notesLoading: '正在加载注意事项',
    hikoreaLink: '🌐 前往 Hi Korea 在线申请',
    hikoreaToast: '正在前往 Hi Korea 指南页面',
    portalToast: '正在前往学校门户网站',
    portalLink: '🏫 前往学校门户网站',
  },

  checklist: {
    createdTitle: '{title}清单',
    total: '共 {n} 项',
    navTitle: '清单',
    navSub: '{title} · {n} 项',
    askBody: '要根据这些内容创建清单吗？',
    make: '创建',
    generatedBody: '清单已创建。\n要将其添加到日历吗？',
    selectSubtitle: '请选择要添加到日历的项目',
    selectAll: '全选',
    deselectAll: '取消全选',
    linkN: '添加 {n} 项',
    selectPrompt: '请选择项目',
  },

  calendarLink: {
    label: '添加到日历',
    body: '要将这些日程添加到日历吗？',
    doneLabel: '已添加',
    goBody: '要立即前往日历吗？',
  },

  source: { title: '📎 来源' },

  kb: {
    channelLabel: '{name}频道',
    originalQ: 'Q. 原始问题',
    answerBody: '以下是 D-2 签证延期所需材料。可前往出入境管理事务所现场申请，也可通过 Hi Korea 在线申请。',
    requiredDocs: '📋 所需材料',
    docs: [
      '护照原件 + 复印件 1 份（有效期 6 个月以上）',
      '外国人登录证原件',
      '在读证明（英文）',
      '手续费 60,000 韩元',
    ],
    sourceLine: '📎 来源：{a} · {b}',
    sources: [
      { label: '法务部《出入境管理法施行规则》(2024)', detail: '第76条 – 变更·延长居留资格的程序及提交材料' },
      { label: 'Hi Korea 外国人指南', detail: 'www.hikorea.go.kr · 签证延期在线申请指南' },
    ],
    actionGuide: '⚡ 操作指南',
    ctaTitle: '查看签证延期流程',
    ctaSub: '6 步清单 · 跟踪办理进度',
    related: '🔗 相关问题',
    q1: { q: '延期签证需要准备什么？', preview: 'D-2 签证延期材料如下：① 护照原件 ② 外国人登录证 ③ 在读证明（英文）...' },
    q2: { q: '签证延期什么时候可以申请？', preview: '可在到期日前 4 个月开始申请，最晚请在到期前 1 个月...' },
    q3: { q: '可以通过 Hi Korea 在线申请吗？', preview: '可以，您可以在 Hi Korea (www.hikorea.go.kr) 在线申请签证延期...' },
  },

  search: {
    title: '回答记录',
    subtitle: '搜索 AI 的历史回答',
    bannerPre: '💡 新的问题请在',
    bannerBold: '聊天标签',
    bannerPost: '中提问',
    toChat: '前往聊天 →',
    placeholder: '搜索已保存的回答...',
    filterAll: '全部',
    filter: { all: '全部', visa: '🛂 签证', school: '🏫 学校', job: '💼 就业', house: '🏠 住房' },
    resultCount: '已保存 {n} 条回答',
    aiAnswer: 'AI 回答',
    viewAnswer: '查看回答 ›',
  },

  profile: {
    title: '我的信息',
    noSchool: '暂无学校信息',
    noName: '未填写姓名',
    visaInfo: '🛂 签证信息',
    visaType: '签证类型',
    expiry: '到期日',
    expiryHint: '请在签证频道中填写',
    editVisa: '修改签证信息',
    editVisaToast: '正在前往签证信息修改页面',
    notifSection: '通知设置',
    visaNotif: '签证与居留提醒',
    visaNotifSub: '到期前 90 天·30 天·7 天',
    houseNotif: '租房合同提醒',
    houseNotifSub: '到期前 60 天',
    insNotif: '保险费缴纳提醒',
    insNotifSub: '缴费日前 5 天',
    notifOff: '通知已关闭',
    notifOn: '通知已开启',
    appSection: '应用设置',
    language: '语言',
    languageSheetTitle: '选择语言',
    editProfile: '修改个人信息',
    editProfileSub: '姓名、学校、专业',
    logout: '退出登录',
  },

  onboarding: {
    tagline: '在韩留学，更轻松\n签证、学校、生活，一站式指引',
    basicInfo: '填写基本信息',
    basicNote: '只需填写国籍、学校和签证类型即可开始',
    name: '姓名',
    namePh: '请输入姓名',
    nationality: '国籍',
    nationalityPh: '例如：中国、越南、美国',
    school: '学校',
    schoolPh: '例如：釜山大学',
    department: '专业',
    departmentPh: '例如：计算机工程系',
    grade: '年级',
    visaType: '签证类型',
    visaNote: '📅 签证到期日可以在签证频道聊天时填写',
    languages: '使用语言',
    start: '开始使用 →',
    footnote: '仅凭国籍、学校和签证类型即可自动创建专属频道',
    required: '请填写姓名、学校和签证类型',
  },

  visaTypes: { d2: 'D-2 留学', d4: 'D-4 语言研修', f2: 'F-2 居住', other: '其他' },

  languageNames: { ko: '韩语', zh: '中文', en: '英语', vi: '越南语' },

  bridge: {
    title: '现在起，有任何疑问\n都可以直接提问',
    desc: '签证、校园生活、住房、打工等，\n您可以直接在主聊天中开始提问。\n开始提问后，我们也会为您创建所需的频道。',
    hint1: '签证与居留相关问题',
    hint2: '校园生活、选课、宿舍',
    hint3: '就业许可、打工规定',
    start: '开始主聊天 →',
    home: '先看看首页',
  },

  // ───────────── 数据翻译（覆盖韩文原文）─────────────

  channels: {
    visa: {
      name: '签证与居留',
      welcome: '这里是“签证与居留”频道。\n我会为您介绍 ARC 重新登记、签证延期、外国人登录证相关办理流程。',
      placeholder: '咨询签证相关问题...',
      qa: {
        0: { label: '📋 签证延期流程' },
        1: { label: '🪪 补办外国人登录证' },
        2: { label: '📄 居留证明', text: '请问如何办理居留证明？' },
        3: { label: '🔄 变更签证', text: '请问变更签证的流程是什么？' },
      },
    },
    school: {
      name: '校园生活',
      welcome: '这里是“校园生活”频道。\n我会分步骤为您介绍选课、校历、奖学金、宿舍等学校相关信息。',
      placeholder: '咨询校园生活相关问题...',
      qa: {
        0: { label: '📋 选课清单' },
        1: { label: '📅 查看校历', text: '请告诉我这学期的校历。' },
        2: { label: '💰 缴纳学费', text: '请问如何缴纳学费？' },
        3: { label: '🎓 奖学金指南', text: '请问留学生如何申请奖学金？' },
      },
    },
    job: {
      name: '就业与打工',
      welcome: '这里是“就业与打工”频道。\n我会分步骤为您介绍兼职就业许可流程、所需材料、可工作时间等。',
      placeholder: '咨询就业、打工相关问题...',
    },
    house: {
      name: '住房',
      welcome: '这里是“住房”频道。欢迎咨询租房合同、管理费、搬家、外国人租房注意事项等住房相关问题！',
      placeholder: '咨询住房相关问题...',
    },
    insurance: {
      name: '医院与保险',
      welcome: '这里是“医院与保险”频道。我会为您介绍健康保险参保、就医方法、保险福利等！',
      placeholder: '咨询医院、保险相关问题...',
    },
    main: {
      name: '主聊天',
      welcome: '您好！有任何问题都可以问我，我会为您推荐合适的频道。',
      placeholder: '有任何问题都可以问...',
    },
  },

  checklists: {
    'arc-renew': {
      title: '外国人登录证补办',
      type: 'ARC 补办',
      items: {
        1: { text: '护照原件', sub: '确认护照仍在有效期内' },
        2: { text: '照片 1 张', sub: '护照用照片 3.5 × 4.5cm' },
        3: { text: '补办申请表', sub: '出入境管理事务所备有，或从 Hi Korea 打印' },
        4: { text: '手续费 30,000 韩元', sub: '请准备现金或银行卡' },
        5: { text: '在 Hi Korea 预约到访', sub: 'www.hikorea.go.kr — 必须预约' },
        6: { text: '前往出入境管理事务所', sub: '请在预约日期携带材料前往' },
        7: { text: '领取新的外国人登录证', sub: '办理时间约 3~5 个工作日' },
      },
    },
    'visa-extension': {
      title: '签证延期',
      type: '签证延期',
      items: {
        1: { text: '护照原件 + 复印件 1 份', sub: '有效期 6 个月以上' },
        2: { text: '外国人登录证原件' },
        3: { text: '开具在读证明（英文）', sub: '门户网站 → 证明书办理 → 英文在读证明' },
        4: { text: '准备手续费 60,000 韩元' },
        5: { text: '预约前往出入境管理事务所', sub: '必须在 Hi Korea 提前预约' },
        6: { text: '现场受理并领取', sub: '办理时间约 5~7 个工作日' },
      },
    },
    'school-registration': {
      title: '选课准备',
      type: '选课',
      items: {
        1: { text: '确认校历', sub: '门户网站 → 校历 → 确认学费缴纳·选课时间' },
        2: { text: '确认学费通知单', sub: '登录门户网站 → 学费通知菜单' },
        3: { text: '缴纳学费', sub: '在缴费期内通过银行转账或门户网站支付' },
        4: { text: '确认选课日期和时间', sub: '不同年级、专业的开始时间可能不同' },
        5: { text: '提前规划课程表', sub: '同时确认专业课/通识课的修读条件' },
        6: { text: '完成选课', sub: '在学校门户网站申请想上的课程' },
        7: { text: '确认选课结果', sub: '查询结果后，可在改选期间进行变更' },
      },
    },
  },

  mock: {
    sources: {
      visa: {
        0: { label: '法务部《出入境管理法施行规则》(2024)', detail: '第76条 – 变更·延长居留资格的程序及提交材料' },
        1: { label: 'Hi Korea 外国人综合指南', detail: 'www.hikorea.go.kr · 签证延期在线申请指南' },
      },
      school: {
        0: { label: '釜山大学学事运营规定', detail: '第12条 – 选课及变更程序' },
      },
      job: {
        0: { label: '《出入境管理法施行令》第23条', detail: '留学生兼职就业许可标准（每周 20 小时）' },
      },
      house: {
        0: { label: '《住宅租赁保护法》第3条', detail: '迁入申报及确定日期的要件' },
      },
      insurance: {
        0: { label: '《国民健康保险法施行令》', detail: '外国留学生强制参保标准（居留 6 个月以上）' },
      },
    },
    answers: {
      visa: {
        0: 'ARC 重新登记时，一般需要准备以下材料。\n\n1. 护照（确认有效期）\n2. 外国人登录证\n3. 在读证明\n4. 居住地相关材料（如需要）\n5. 手续费\n\n补充说明：\n- 可通过 Hi Korea 在线申请，也可前往出入境管理事务所现场申请。\n- 请务必在签证到期前提前申请。\n\n#ARC #重新登记 #签证 #HiKorea',
        1: '如果外国人登录证丢失了，请按以下顺序办理。\n\n1. 确认丢失后，准备申请补办\n2. 准备护照、照片、补办申请表等所需材料\n3. 在 Hi Korea 预约到访\n4. 前往出入境管理事务所申请补办\n5. 领取新的外国人登录证\n\n注意事项：\n- 丢失后请不要搁置太久。\n- 可能需要核实身份，请同时携带护照。\n\n需要我把要准备的材料整理成清单吗？\n\n#外国人登录证 #丢失 #补办 #出入境',
        2: 'D-2 签证延期通常按以下顺序办理。\n\n1. 准备护照、外国人登录证、在读证明等基本材料\n2. 在 Hi Korea 确认是否可在线申请，或预约到访\n3. 前往出入境管理事务所或在线提交\n4. 缴纳手续费并完成受理\n5. 确认办理结果\n\n注意事项：\n- 请务必在签证到期前提前申请。\n- 部分学校可能需要额外材料。\n\n#D-2 #签证延期 #材料 #HiKorea',
        3: 'D-2（留学）签证是为在韩国攻读正规学位课程而设的签证。\n\n主要特点：\n- 居留期限：在读期间（可延期）\n- 对象：入读专科以上正规学位课程的学生\n- 就业：经许可可每周兼职最多 20 小时\n\n⚠️ 最新信息请在 Hi Korea (hikorea.go.kr) 确认。\n\n#D-2签证 #留学签证 #签证信息',
        4: '这是持 D-2（留学）签证的留学生兼职就业许可条件。\n\n主要条件：\n- 学期中：每周最多 20 小时\n- 假期中：不限时间\n- 必须取得法务部兼职就业许可（未经许可就业可能被取消签证）\n\n申请方式：\n- 通过 Hi Korea (hikorea.go.kr) 在线申请，或前往出入境管理事务所办理\n\n⚠️ D-4 签证原则上不可就业（需另行获得许可）\n\n#兼职就业 #留学生打工 #就业许可',
      },
      school: {
        0: '选课之前，建议先做好以下准备。\n\n1. 确认能登录学校门户网站\n2. 确认选课日期\n3. 提前规划课程表\n4. 确认专业课/通识课的修读条件\n\n补充说明：\n- 请在选课开始时间准时快速操作。\n- 热门课程可能很快就会满员。\n- 在改选期间可以进行变更。\n\n需要我把准备步骤整理成清单吗？\n\n#选课 #校园生活 #校历',
        1: '为下学期做准备时，建议把缴纳学费和选课分开确认。\n\n1. 在校历中确认学费缴纳期间\n2. 确认学费通知单并缴费\n3. 确认选课期间\n4. 在学校门户网站搜索想上的课程\n5. 选课完成后确认课程表\n6. 如有需要，在改选期间进行变更\n\n注意事项：\n- 学费缴纳期间和选课期间可能不同。\n- 留学生最好同时关注国际处的公告。\n\n需要我把准备步骤整理成清单吗？\n\n#学费 #选课 #校历 #校园生活',
      },
      job: {
        0: '留学生想开始打工，首先需要获得兼职就业许可。\n\n1. 前往出入境管理事务所或通过 Hi Korea 在线申请\n2. 准备在读证明 + 成绩单 + 护照 + 外国人登录证\n3. 领取许可证后即可就业\n\n以 D-2 签证为准，学期中每周最多 20 小时，假期中每周最多 40 小时。\n\n#打工 #兼职就业 #留学生',
        1: '非法就业可能被取消签证并被强制出境，请务必获得许可后再就业。\n\n#注意事项 #就业规定',
      },
      house: {
        0: '签订全租或月租合同前，请务必确认不动产登记簿。一定要检查是否设有抵押权。\n\n#全租 #月租 #合同注意',
        1: '迁入申报需在签订合同后 14 天内到居民中心办理，才能受到法律保护。\n\n#迁入申报 #居住权益',
      },
      insurance: {
        0: '留学生保险的参保方式可能因学校公告或保险政策而不同。\n以下是需要按最新标准确认的事项。\n\n1. 确认釜山大学国际处或相关部门的公告\n2. 确认是否属于留学生保险参保对象\n3. 确认参保期间和保险费\n4. 确认提交材料或是否可在线申请\n5. 参保完成后保管好凭证\n\n⚠️ 这可能是目前数据库中没有的最新信息，请以官方公告为准。\n\n#留学生保险 #釜山大学 #最新公告 #需要网络搜索',
        1: '在韩居留 6 个月以上的外国留学生必须参加健康保险。\n可在国民健康保险公团 (nhis.or.kr) 在线申请参保。\n\n#健康保险 #留学生必须参保',
      },
      main: {
        0: 'ARC 重新登记需要同时确认所需材料和申请流程。\n我会在“签证与居留”频道为您分步骤详细介绍。',
        1: '选课需要同时确认校历和申请方法。\n我会在“校园生活”频道为您分步骤介绍。',
        2: 'D-2 签证延期需要同时确认所需材料和申请流程。\n我会在“签证与居留”频道为您分步骤介绍。',
        3: '外国人登录证丢失后，需要尽快申请补办。\n我会在“签证与居留”频道为您整理挂失和补办流程。',
        4: '这个问题同时涉及校历中的学费缴纳和选课。\n我会在“校园生活”频道把时间安排和流程一并为您介绍。',
        5: '这个问题需要确认最新公告。\n由于可能不在现有数据中，或标准可能已变更，我会引导您在“医院与保险”频道确认最新信息。',
        6: '兼职就业许可条件可以直接在“就业与打工”频道确认。\n我会在频道中详细介绍许可流程和注意事项。',
        7: 'D-2（留学）签证是为在韩国大学、研究生院攻读正规学位课程而设的签证。\n您可以在“签证与居留”频道进一步了解其特点和条件。',
      },
    },
  },
};
