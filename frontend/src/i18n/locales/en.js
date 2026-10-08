/**
 * English
 *
 * 위쪽은 ko.js 와 같은 구조의 UI 문구,
 * 아래쪽(checklists / channels / mock)은 데이터 파일의 한국어 원문을 덮어쓰는 번역이다.
 */
export default {
  meta: { code: 'en', name: 'English', nativeName: 'English', tag: 'en-US' },

  common: {
    ragActive: 'RAG on',
    yes: 'Yes',
    no: 'No',
    close: 'Close',
    cancel: 'Cancel',
    example: 'Sample',
    gradeN: 'Year {n}',
    thinking: '…',
  },

  nav: { home: 'Home', chat: 'Chat', calendar: 'Calendar', history: 'History', profile: 'Profile' },

  splash: { tagline: 'Your guide to student life in Korea' },

  toast: {
    notifSoon: 'Opening notifications',
    allStepsDone: '🎉 You completed every step!',
    schoolDone: '🎉 Course registration prep is all done!',
    arcDone: '🎉 Reissue prep is all done!',
    filterApplied: '{name} filter applied',
    relatedLoading: 'Loading related questions',
    calendarLinked: '📅 Added to your calendar!',
  },

  tags: {
    d2: '#D-2', extend: '#Extension', docs: '#Documents', immigration: '#Immigration', period: '#Period',
  },

  time: { today: 'Today', justNow: 'Just now', daysAgo: '{n}d ago', weeksAgo: '{n}w ago' },

  home: {
    notifSoon: 'Notifications are coming soon',
    greeting: 'Hello, {name}!',
    greetingFallback: 'Welcome',
    urgentLabel: '🚨 Needs attention',
    urgentTitle: 'Visa expiring soon',
    urgentPreview: 'D-87 — Start preparing your extension documents now',
    itemIsExample: 'This item is a sample',
    myChannels: '📂 My channels',
    tapToOpen: 'Tap to open the channel',
    emptyTitle: 'No channels yet',
    emptyDesc: 'Pick a topic in Main Chat\nand a channel will be created.',
    startInMain: '💬 Start in Main Chat',
    belowAreExamples: 'Samples below',
    channelIsExample: 'This channel is a sample',
    newChannel: 'Create a new channel',
    newChannelSub: 'Choose a topic in Main Chat',
    ghost: {
      visa: 'Visa extension, length of stay, alien registration',
      school: 'Course registration, academic calendar, dorms, scholarships',
      job: 'Part-time work permits, internships, work rules',
      house: 'Lease contracts, maintenance fees, moving tips',
      insurance: 'Health insurance, hospital visits, benefits',
    },
  },

  chat: {
    subtitle: 'Ask across every channel',
    cat: {
      visa: 'ARC renewal · documents · how to apply',
      job: 'Permit process · documents · cautions',
      school: 'Registration · academic calendar · add/drop',
      house: 'Leases · move-in report · contract tips',
    },
    welcomeTitle: 'What would you like to know?',
    welcomeDesc: 'Pick a topic such as visa, school,\nhousing or part-time work to get started.',
    welcomeBtn: '💬 Go to Main Chat',
    createdSection: '✅ Newly created channels',
    createdPreview: 'Get more detailed answers in the dedicated channel',
    viewInChannel: 'channel — see more details',
    channelCreated: '{name} channel created 🎉',
    createTitle: 'Create the {name} channel?',
    createDesc: 'You will get more detailed,\nspecialized answers.',
    createBtn: 'Create channel',
    later: 'Not now',
    error: 'Something went wrong while loading the response. Please try again shortly.',
  },

  channel: {
    chatTab: '💬 Chat',
    knowledgeTab: '📚 Knowledge cards',
    searchInChannel: 'Search this channel...',
    checklist: '📋 Checklist',
  },

  visa: {
    expires: '🗓 {type} expires',
    alarmOn: '🔔 Reminders on',
    backToChannel: 'Visa channel',
  },

  calendar: {
    title: 'Calendar',
    today: 'Today',
    emptyTitle: 'No events',
    emptySub: 'Create a checklist in chat and\nadd it to your calendar',
    fromChat: 'This event was added from chat',
    chatBadge: '💬 Chat',
    viewChat: '💬 View related conversation',
    addToGoogle: '📅 Add to Google Calendar',
    done: 'Done',
  },

  guide: {
    progress: '{done} / {total} steps done',
    groupProgress: '{done}/{total} done',
    docsPrep: '📁 Documents',
    apply: '📋 Apply',
    regPrep: '📅 Getting ready',
    courseReg: '📋 Course registration',
    autoSave: '✅ Your progress saves automatically, even if you close the app.',
    visaTitle: 'D-2 visa extension steps',
    arcTitle: 'Alien registration card reissue steps',
    schoolTitle: 'Course registration & enrollment',
    officeBasis: 'For in-person visits to the immigration office',
    schoolBasis: 'Based on the school portal · Check before the semester starts',
    schoolChannel: 'School life channel',
    moreNotes: '⚠️ More notes',
    notesLoading: 'Loading notes',
    hikoreaLink: '🌐 Apply online at Hi Korea',
    hikoreaToast: 'Opening the Hi Korea guide page',
    portalToast: 'Opening the school portal',
    portalLink: '🏫 Go to the school portal',
  },

  checklist: {
    createdTitle: '{title} checklist',
    total: '{n} items in total',
    navTitle: 'Checklist',
    navSub: '{title} · {n} items',
    askBody: 'Create a checklist from this?',
    make: 'Create',
    generatedBody: 'Your checklist has been created.\nAdd it to your calendar?',
    selectSubtitle: 'Choose the items to add to your calendar',
    selectAll: 'Select all',
    deselectAll: 'Clear all',
    linkN: 'Add {n} items',
    selectPrompt: 'Select items',
    exportIcs: '📥 Export {n} selected as .ics (Google Calendar, etc.)',
  },

  calendarLink: {
    label: 'Add to calendar',
    body: 'Add these events to your calendar?',
    doneLabel: 'Added',
    goBody: 'Go to the calendar now?',
  },

  source: { title: '📎 Sources' },

  kb: {
    channelLabel: '{name} channel',
    originalQ: 'Q. Original question',
    answerBody: 'These are the documents needed for a D-2 visa extension. You can apply in person at the immigration office or online through Hi Korea.',
    requiredDocs: '📋 Required documents',
    docs: [
      'Original passport + 1 copy (valid for 6+ months)',
      'Original alien registration card',
      'Certificate of enrollment (English)',
      'Fee: KRW 60,000',
    ],
    sourceLine: '📎 Sources: {a} · {b}',
    sources: [
      { label: 'Ministry of Justice, Immigration Control Act Enforcement Rules (2024)', detail: 'Article 76 – Procedure and documents for changing/extending status of stay' },
      { label: 'Hi Korea Foreigner Guide', detail: 'www.hikorea.go.kr · Online visa extension guide' },
    ],
    actionGuide: '⚡ Action Guide',
    ctaTitle: 'View extension steps',
    ctaSub: '6-step checklist · track your progress',
    related: '🔗 Related questions',
    q1: { q: 'What do I need to extend my visa?', preview: 'Documents for a D-2 extension: ① original passport ② alien registration card ③ certificate of enrollment (English)...' },
    q2: { q: 'When can I apply for a visa extension?', preview: 'You can apply from 4 months before expiry. At the latest, 1 month before it expires...' },
    q3: { q: 'Can I apply online through Hi Korea?', preview: 'Yes, you can apply for a visa extension online at Hi Korea (www.hikorea.go.kr)...' },
  },

  search: {
    title: 'Answer history',
    subtitle: 'Search past AI answers',
    bannerPre: '💡 Ask new questions in the',
    bannerBold: 'Chat tab',
    bannerPost: '',
    toChat: 'Go to chat →',
    placeholder: 'Search saved answers...',
    filterAll: 'All',
    filter: { all: 'All', visa: '🛂 Visa', school: '🏫 School', job: '💼 Jobs', house: '🏠 Housing' },
    resultCount: '{n} saved answers',
    aiAnswer: 'AI answer',
    viewAnswer: 'View answer ›',
    empty: 'No answers match this filter',
  },

  profile: {
    title: 'My profile',
    noSchool: 'No school info',
    noName: 'No name',
    visaInfo: '🛂 Visa info',
    visaType: 'Visa type',
    expiry: 'Expiry date',
    expiryHint: 'Enter it in the Visa channel',
    editVisa: 'Edit visa info',
    editVisaToast: 'Opening visa info editor',
    notifSection: 'Notifications',
    visaNotif: 'Visa & stay reminders',
    visaNotifSub: '90, 30 and 7 days before expiry',
    houseNotif: 'Housing contract reminders',
    houseNotifSub: '60 days before expiry',
    insNotif: 'Insurance payment reminders',
    insNotifSub: '5 days before the due date',
    notifOff: 'Notifications turned off',
    notifOn: 'Notifications turned on',
    appSection: 'App settings',
    language: 'Language',
    languageSheetTitle: 'Choose language',
    editProfile: 'Edit personal info',
    editProfileSub: 'Name, school, major',
    logout: 'Log out',
  },

  onboarding: {
    tagline: 'Studying in Korea, made easier\nVisa, school and daily life — all in one guide',
    basicInfo: 'Basic information',
    basicNote: 'Just enter your nationality, school and visa type to get started',
    name: 'Name',
    namePh: 'Enter your name',
    nationality: 'Nationality',
    nationalityPh: 'e.g. China, Vietnam, USA',
    school: 'School',
    schoolPh: 'e.g. Pusan National University',
    department: 'Major',
    departmentPh: 'e.g. Computer Science',
    grade: 'Year',
    visaType: 'Visa type',
    visaNote: '📅 You can enter your visa expiry date while chatting in the Visa channel',
    languages: 'Languages you use',
    start: 'Get started →',
    footnote: 'Channels are created automatically from your nationality, school and visa type',
    required: 'Please enter your name, school and visa type',
  },

  visaTypes: { d2: 'D-2 Student', d4: 'D-4 Language course', f2: 'F-2 Resident', other: 'Other' },

  languageNames: { ko: 'Korean', zh: 'Chinese', en: 'English', vi: 'Vietnamese' },

  bridge: {
    title: 'You can now ask\nanything right away',
    desc: 'Visa, school life, housing, part-time jobs and more —\nstart in Main Chat right away.\nWe will create the channels you need as you ask.',
    hint1: 'Visa & stay questions',
    hint2: 'School life, course registration, dorms',
    hint3: 'Work permits, part-time job rules',
    start: 'Start Main Chat →',
    home: 'Look around Home first',
  },

  // ───────────── 데이터 번역 (한국어 원문을 덮어씀) ─────────────

  channels: {
    visa: {
      name: 'Visa & Stay',
      welcome: 'Welcome to the Visa & Stay channel.\nI can guide you through ARC re-registration, visa extensions and alien registration card procedures.',
      placeholder: 'Ask about visas...',
      qa: {
        0: { label: '📋 Visa extension steps' },
        1: { label: '🪪 Reissue alien registration card' },
        2: { label: '📄 Certificate of residence', text: 'How do I get a certificate of residence?' },
        3: { label: '🔄 Change of visa', text: 'What is the procedure for changing my visa?' },
      },
    },
    school: {
      name: 'School Life',
      welcome: 'Welcome to the School Life channel.\nI will guide you step by step through course registration, the academic calendar, scholarships, dorms and more.',
      placeholder: 'Ask about school life...',
      qa: {
        0: { label: '📋 Course registration checklist' },
        1: { label: '📅 Academic calendar', text: 'What is the academic calendar for this semester?' },
        2: { label: '💰 Paying tuition', text: 'How do I pay my tuition?' },
        3: { label: '🎓 Scholarships', text: 'How can international students apply for scholarships?' },
      },
    },
    job: {
      name: 'Jobs & Part-time Work',
      welcome: 'Welcome to the Jobs & Part-time Work channel.\nI will guide you step by step through the part-time work permit process, required documents and allowed working hours.',
      placeholder: 'Ask about jobs and part-time work...',
      qa: {
        0: { label: '🪪 Work permit', text: 'How do I apply for a part-time work permit?' },
        1: { label: '📄 Required documents', text: 'What documents do I need for a part-time job?' },
        2: { label: '⏰ Allowed hours', text: 'How many hours can I work part-time during the semester?' },
        3: { label: '⚠️ Working without permission', text: 'What happens if I work without a permit?' },
      },
    },
    house: {
      name: 'Housing',
      welcome: 'Welcome to the Housing channel. Ask me about jeonse/monthly rent contracts, maintenance fees, moving, and tips for foreign tenants!',
      placeholder: 'Ask about housing...',
      qa: {
        0: { label: '📑 Before you sign', text: 'What should I check before signing a lease?' },
        1: { label: '🏠 Move-in report', text: 'How do I file a move-in report?' },
        2: { label: '💰 Maintenance fees', text: 'What does the maintenance fee usually cover?' },
        3: { label: '📦 Moving checklist', text: 'What should I watch out for when moving?' },
      },
    },
    insurance: {
      name: 'Hospital & Insurance',
      welcome: 'Welcome to the Hospital & Insurance channel. I can help with health insurance enrollment, using hospitals and insurance benefits!',
      placeholder: 'Ask about hospitals and insurance...',
      qa: {
        0: { label: '🏥 Enrolling in insurance', text: 'How do international students enroll in health insurance?' },
        1: { label: '💳 Paying premiums', text: 'How do I pay my health insurance premium?' },
        2: { label: '🩺 Using hospitals', text: 'How does seeing a doctor work in Korea?' },
        3: { label: '📋 Insurance benefits', text: 'What benefits does health insurance cover?' },
      },
    },
    main: {
      name: 'Main Chat',
      welcome: 'Hello! Ask me anything. I will point you to the right channel.',
      placeholder: 'Ask anything...',
    },
  },

  checklists: {
    'arc-renew': {
      title: 'Alien registration card reissue',
      type: 'ARC reissue',
      items: {
        1: { text: 'Original passport', sub: 'Check that it is still valid' },
        2: { text: '1 photo', sub: 'Passport-style photo, 3.5 × 4.5 cm' },
        3: { text: 'Reissue application form', sub: 'Available at the immigration office or print from Hi Korea' },
        4: { text: 'Fee: KRW 30,000', sub: 'Prepare cash or a card' },
        5: { text: 'Book a visit on Hi Korea', sub: 'www.hikorea.go.kr — reservation required' },
        6: { text: 'Visit the immigration office', sub: 'Bring your documents on the reserved date' },
        7: { text: 'Receive your new card', sub: 'Processing takes about 3–5 business days' },
      },
    },
    'visa-extension': {
      title: 'Visa extension',
      type: 'Visa extension',
      items: {
        1: { text: 'Original passport + 1 copy', sub: 'Valid for 6+ months' },
        2: { text: 'Original alien registration card' },
        3: { text: 'Certificate of enrollment (English)', sub: 'Portal → Certificates → English enrollment certificate' },
        4: { text: 'Prepare the KRW 60,000 fee' },
        5: { text: 'Book an immigration office visit', sub: 'Reservation on Hi Korea is required' },
        6: { text: 'Submit in person and collect', sub: 'Processing takes about 5–7 business days' },
      },
    },
    'school-registration': {
      title: 'Course registration prep',
      type: 'Course registration',
      items: {
        1: { text: 'Check the academic calendar', sub: 'Portal → Academic calendar → tuition and registration periods' },
        2: { text: 'Check your tuition bill', sub: 'Log in to the portal → Tuition notice menu' },
        3: { text: 'Pay tuition', sub: 'Bank transfer or portal payment within the payment period' },
        4: { text: 'Check registration date and time', sub: 'Start times can differ by year and department' },
        5: { text: 'Plan your timetable in advance', sub: 'Also check major/elective requirements' },
        6: { text: 'Complete registration', sub: 'Register for your courses on the school portal' },
        7: { text: 'Check the results', sub: 'You can change courses during the add/drop period' },
      },
    },
  },

  mock: {
    sources: {
      visa: {
        0: { label: 'Ministry of Justice, Immigration Control Act Enforcement Rules (2024)', detail: 'Article 76 – Procedure and documents for changing/extending status of stay' },
        1: { label: 'Hi Korea Comprehensive Foreigner Guide', detail: 'www.hikorea.go.kr · Online visa extension guide' },
      },
      school: {
        0: { label: 'Pusan National University Academic Regulations', detail: 'Article 12 – Course registration and changes' },
      },
      job: {
        0: { label: 'Immigration Control Act Enforcement Decree, Art. 23', detail: 'Part-time work permit criteria for students (20 hrs/week)' },
      },
      house: {
        0: { label: 'Housing Lease Protection Act, Art. 3', detail: 'Move-in report and fixed-date requirements' },
      },
      insurance: {
        0: { label: 'National Health Insurance Act Enforcement Decree', detail: 'Mandatory enrollment for international students (stay of 6+ months)' },
      },
    },
    answers: {
      visa: {
        0: 'Here are the documents you generally need for ARC re-registration.\n\n1. Passport (check validity)\n2. Alien registration card\n3. Certificate of enrollment\n4. Proof of residence (if required)\n5. Fee\n\nAdditional notes:\n- You can apply online via Hi Korea or in person at the immigration office.\n- It is important to apply before your visa expires.\n\n#ARC #Re-registration #Visa #HiKorea',
        1: 'If you lost your alien registration card, follow these steps.\n\n1. Confirm the loss and get ready to apply for a reissue\n2. Prepare your passport, photo, reissue form and other documents\n3. Book a visit on Hi Korea\n4. Visit the immigration office and apply for reissue\n5. Receive your new card\n\nNotes:\n- Do not leave a lost card unreported for long.\n- You may need ID, so keep your passport with you.\n\nWould you like me to turn the documents you need into a checklist?\n\n#AlienRegistrationCard #Lost #Reissue #Immigration',
        2: 'A D-2 visa extension usually goes like this.\n\n1. Prepare basic documents: passport, alien registration card, certificate of enrollment\n2. Check whether you can apply online on Hi Korea, or book a visit\n3. Visit the immigration office or submit online\n4. Pay the fee and complete the submission\n5. Check the result\n\nNotes:\n- Apply before your visa expires.\n- Some schools may require additional documents.\n\n#D-2 #VisaExtension #Documents #HiKorea',
        3: 'The D-2 (study) visa is for completing a regular degree program in Korea.\n\nKey points:\n- Period of stay: length of enrollment (extendable)\n- Eligible: students admitted to a regular degree program at a college or above\n- Work: part-time work of up to 20 hours a week with permission\n\n⚠️ Check the latest details on Hi Korea (hikorea.go.kr).\n\n#D-2Visa #StudentVisa #VisaInfo',
        4: 'These are the conditions for part-time work permits for students holding a D-2 (study) visa.\n\nMain conditions:\n- During the semester: up to 20 hours a week\n- During breaks: no hourly limit\n- A Ministry of Justice part-time work permit is required (working without one can lead to visa cancellation)\n\nHow to apply:\n- Online via Hi Korea (hikorea.go.kr) or in person at the immigration office\n\n⚠️ Work is generally not allowed on a D-4 visa (separate permission required)\n\n#PartTimeWork #StudentJobs #WorkPermit',
      },
      school: {
        0: 'It helps to prepare the following before course registration.\n\n1. Make sure you can log in to the school portal\n2. Check your registration date\n3. Plan your timetable in advance\n4. Check major/elective requirements\n\nAdditional notes:\n- It is important to register quickly once registration opens.\n- Popular courses can fill up fast.\n- You can make changes during the add/drop period.\n\nWould you like me to turn the preparation steps into a checklist?\n\n#CourseRegistration #SchoolLife #AcademicCalendar',
        1: 'For next semester, it helps to handle tuition payment and course registration separately.\n\n1. Check the tuition payment period in the academic calendar\n2. Check your tuition bill and pay it\n3. Check the course registration period\n4. Search for the courses you want on the school portal\n5. Check your timetable after registering\n6. Make changes during the add/drop period if needed\n\nNotes:\n- The tuition payment period and course registration period may differ.\n- International students should also check announcements from the international office.\n\nWould you like me to turn the preparation steps into a checklist?\n\n#Tuition #CourseRegistration #AcademicCalendar #SchoolLife',
      },
      job: {
        0: 'To start a part-time job, international students first need a part-time work permit.\n\n1. Visit the immigration office or apply online via Hi Korea\n2. Prepare your certificate of enrollment, transcript, passport and alien registration card\n3. You can start working after receiving the permit\n\nOn a D-2 visa you can work up to 20 hours a week during the semester and up to 40 hours a week during breaks.\n\n#PartTime #WorkPermit #InternationalStudent',
        1: 'Working illegally can lead to visa cancellation and deportation, so always get a permit before you start.\n\n#Caution #WorkRules',
      },
      house: {
        0: 'Before signing a jeonse or monthly rent contract, be sure to check the property register. You must check whether there is a mortgage on the property.\n\n#Jeonse #MonthlyRent #ContractTips',
        1: 'To be legally protected, you must file a move-in report at the community center within 14 days of signing the contract.\n\n#MoveInReport #HousingRights',
      },
      insurance: {
        0: 'How to enroll in student insurance can vary by school notice and insurance policy.\nThese are the items that need checking against the latest rules.\n\n1. Check announcements from the Pusan National University international office or related department\n2. Confirm whether you are eligible for student insurance\n3. Check the enrollment period and premium\n4. Check required documents or whether you can apply online\n5. Keep proof after enrolling\n\n⚠️ This may be newer than the information in our database, so please check the official announcement.\n\n#StudentInsurance #PNU #LatestNotice #NeedsWebSearch',
        1: 'International students staying 6 months or longer must enroll in health insurance.\nYou can apply online at the National Health Insurance Service (nhis.or.kr).\n\n#HealthInsurance #MandatoryForStudents',
      },
      main: {
        0: 'For ARC re-registration you need to check both the documents and the application steps.\nI will guide you step by step in the Visa & Stay channel.',
        1: 'For course registration you need to check both the academic calendar and how to apply.\nI will guide you step by step in the School Life channel.',
        2: 'For a D-2 visa extension you need to check both the documents and the application steps.\nI will guide you step by step in the Visa & Stay channel.',
        3: 'If you lost your alien registration card, you should apply for a reissue quickly.\nI will walk you through reporting and reissuing in the Visa & Stay channel.',
        4: 'This question covers both tuition payment and course registration in the academic calendar.\nI will guide you through the schedule and steps together in the School Life channel.',
        5: 'This question needs the latest announcements.\nSince it may not be in our data or the rules may have changed, I will guide you to check the latest information in the Hospital & Insurance channel.',
        6: 'You can check part-time work permit conditions right away in the Jobs & Part-time Work channel.\nThe channel explains the permit process and cautions in detail.',
        7: 'The D-2 (study) visa is for completing a regular degree program at a Korean university or graduate school.\nYou can check its features and conditions in more detail in the Visa & Stay channel.',
      },
    },
  },
};
