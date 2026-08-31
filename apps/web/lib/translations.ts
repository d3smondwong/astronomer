export type Language = 'en' | 'ch';

export const translations = {
  header: {
    signIn:      { en: 'Sign In',           ch: '登录' },
    loginSignUp: { en: 'Log in or sign up', ch: '登录或注册' },
    signOut:     { en: 'Sign out',          ch: '退出' },
    langToggle:  { en: '中文',              ch: 'English' },
  },
  auth: {
    loginTitle:          { en: 'Log in or sign up',         ch: '登录或注册' },
    // Contextual modal copy, keyed by the reason the auth modal was opened.
    loginSubtitle:        { en: 'Unlock insights about your life', ch: '解锁专属您的人生洞察' },
    addChartTitle:        { en: 'Unlock Unlimited Charts', ch: '解锁无限命盘' },
    addChartSubtitle:     { en: 'Save multiple profiles to your dashboard and claim your free premium insights', ch: '将多个命盘保存至您的仪表板，并领取免费高级解析' },
    pendingChartTitle:    { en: 'Secure your chart', ch: '保存您的命盘' },
    pendingChartSubtitle: { en: "Don't lose this chart. Create a free account to instantly save it and claim your free premium insights.", ch: '切勿丢失此命盘。注册免费账户即可立即保存，并领取免费高级解析。' },
    insightsTitle:        { en: 'Reveal detailed insights about your life', ch: '揭示关于您人生的详细洞察' },
    insightsSubtitle:     { en: 'Create a free account to reveal insights into your personality, career and wealth paths', ch: '注册免费账户，揭示您的性格、事业与财富之路的洞察' },
    emailPlaceholder:    { en: 'Email',                     ch: '邮箱' },
    passwordPlaceholder: { en: 'Password',                  ch: '密码' },
    continueBtn:         { en: 'Continue',                  ch: '继续' },
    loading:             { en: 'Loading…',                  ch: '加载中…' },
    unlockInsights:      { en: 'Sign up to reveal your Personality Profile', ch: '注册以解锁个性分析' },
    createFreeAccount:   { en: 'Create Free Account',       ch: '免费注册' },
    generatingInsights:  { en: 'Generating your insights…', ch: '正在生成分析…' },
    generateInsights:    { en: 'Generate Insights',         ch: '生成分析' },
    migrateFailed:       { en: "Successfully signed in. We were unable to securely save the chart you made as a guest. Please re-generate it to keep it on your account.", ch: '您已成功登录。未能安全保存您以访客身份生成的命盘，请重新生成以保存至您的账户。' },
    // Two session-failure strings, not one: the recovery differs by where it fires.
    // In AuthModal the modal stays open, so the user retries with the Continue button.
    sessionError:        { en: "We're having trouble keeping you signed in. Please select Continue to try again.", ch: '登录状态保持遇到问题，请点击「继续」重试。' },
    // On the landing form the chart has ALREADY been created and saved — only the
    // session cookie refresh failed. Saying so prevents a duplicate re-generation.
    sessionErrorChartSaved: { en: "Your chart is saved, but we're having trouble keeping you signed in. Please refresh the page to open it.", ch: '您的命盘已保存，但登录状态保持遇到问题。请刷新页面以查看。' },
  },
  profile: {
    // Day Master badge
    dayMasterBadge:   { en: 'Day Master',        ch: '日主' },
    // PillarCard section labels
    heavenlyStem:     { en: 'Heavenly Stem',     ch: '天干' },
    earthlyBranch:    { en: 'Earthly Branch',    ch: '地支' },
    voidLabel:        { en: 'Void',              ch: '空亡' },
    primaryVoid:      { en: 'Primary Void',     ch: '空亡' },
    mutualVoid:       { en: 'Mutual Void',      ch: '互换空亡' },
    rootingDeep:      { en: 'Deeply Rooted',    ch: '深根' },
    rootingModerate:  { en: 'Moderately Rooted', ch: '中根' },
    rootingLight:     { en: 'Lightly Rooted',   ch: '浅根' },
    rootingNone:      { en: 'No Root',          ch: '无根' },
    hiddenStems:      { en: 'Hidden Stems',      ch: '地支藏干' },
    primaryQi:        { en: 'Primary Qi',        ch: '本气' },
    middleQi:         { en: 'Middle Qi',         ch: '中气' },
    residualQi:       { en: 'Residual Qi',       ch: '余气' },
    noneLabel:        { en: 'None',              ch: '无' },
    voidBranchPairs:  { en: 'Void Branch Pairs', ch: '空亡支' },
    twelveLifeStages: { en: '12 Life Stages',    ch: '十二长生' },
    dayMasterRef:     { en: 'Day Master',        ch: '日主' },
    pillarStemRef:    { en: "Pillar's Stem",     ch: '柱干' },
    naYin:            { en: 'Na Yin',            ch: '纳音' },
    shenSha:          { en: 'Shen Sha',          ch: '神煞' },
    // Tab labels
    tabFourPillars:   { en: 'Four Pillars',      ch: '四柱' },
    tabCycles:        { en: 'Cycles',            ch: '大运流年' },
    tabInsights:      { en: 'Insights',          ch: '命盘解析' },
    // Relationship labels
    relAncestry:      { en: 'ANCESTRY',          ch: '祖先' },
    relParents:       { en: 'PARENTS',           ch: '父母' },
    relSelf:          { en: 'SELF',              ch: '自我' },
    relChildren:      { en: 'CHILDREN',          ch: '子女' },
    // Pillar names
    yearPillar:       { en: 'Year Pillar',       ch: '年柱' },
    monthPillar:      { en: 'Month Pillar',      ch: '月柱' },
    dayPillar:        { en: 'Day Pillar',        ch: '日柱' },
    hourPillar:       { en: 'Hour Pillar',       ch: '时柱' },
    // Elements tab
    elementDistrib:   { en: 'Element Distribution',               ch: '五行分布' },
    fiveElementBal:   { en: 'Your Five Element Balance',          ch: '五行平衡' },
    elementStrength:  { en: 'Element Strength',                   ch: '五行强弱' },
    comparativeView:  { en: 'Comparative View',                   ch: '对比视图' },
    luckyElements:    { en: 'Elemental Balance',                  ch: '用神' },
    luckyElemDesc:    { en: 'Elements that can bring balance to your chart', ch: '可为命盘带来平衡的五行' },
    // Favorable elements (用神/调候) card
    favorableLabel:   { en: 'Favorable',                          ch: '喜用' },
    unfavorableLabel: { en: 'Unfavorable',                        ch: '忌' },
    climateLabel:     { en: 'Climate Needs',                      ch: '调候' },
    // 五神 role labels — the 用神 headline + its supporting cast (see FavorableElementsCard)
    usefulGodLabel:   { en: 'Useful God',                         ch: '用神' },
    helpfulLabel:     { en: 'Helpful',                            ch: '喜神' },
    harmfulLabel:     { en: 'Harmful',                            ch: '忌神' },
    feedsHarmLabel:   { en: 'Aggravator',                         ch: '仇神' },
    idleLabel:        { en: 'Idle',                               ch: '闲神' },
    reasonStrong:     { en: 'Your day master is strong — elements that drain and temper it restore balance.', ch: '日主偏旺，宜克泄耗以归中和。' },
    reasonWeak:       { en: 'Your day master is weak — elements that support and strengthen it restore balance.', ch: '日主偏弱，宜生扶以归中和。' },
    reasonBalanced:   { en: 'Your day master is balanced — the season of birth decides which elements serve you best.', ch: '日主中和，喜忌以调候为主。' },
    structCong:       { en: 'Special structure: this chart follows its dominant force — favorable elements come from the structure, not from supporting the day master.', ch: '此局弃命从势，喜忌由格局而定，不以扶抑论。' },
    structZhuanWang:  { en: 'Special structure: one element dominates the chart — going with its flow is favorable, opposing it is not.', ch: '此局一行得气，顺其旺势为喜，逆之为忌。' },
    structHuaQi:      { en: 'Special structure: the day master transforms into another element — favorable elements serve the transformed element.', ch: '日主化气，喜忌以化神为准。' },
    // Insights tab — multi-section report titles
    secPersonality:   { en: 'Core Personality & Character',       ch: '核心性格与品性' },
    secFamily:        { en: 'Family & Upbringing',                ch: '家庭与成长' },
    secRomance:       { en: 'Love, Marriage & Children',          ch: '爱情、婚姻与子女' },
    secCareer:        { en: 'Career & Talents',                   ch: '事业与才能' },
    secWealth:        { en: 'Wealth',                             ch: '财富' },
    // Career section — structured group headings (other Chinese copy is prompt-driven)
    careerPathToSuccess: { en: 'Path to Success',                 ch: '成功之路' },
    careerHighlights:    { en: 'Career Highlights',               ch: '事业亮点' },
    careerChallenges:    { en: 'Career Challenges',               ch: '事业挑战' },
    careerAdvice:        { en: 'Career Advice',                   ch: '事业建议' },
    // Personality section — structured group headings (other Chinese copy is prompt-driven)
    personalityCore:      { en: 'Core Nature',                    ch: '核心本性' },
    personalityMind:      { en: 'How You Think & Feel',           ch: '思维与情感' },
    personalityDrives:    { en: 'What Drives You',                ch: '内在驱动' },
    personalityStrengths: { en: 'Natural Strengths',              ch: '天赋优势' },
    personalityWeakness:  { en: 'Things to Look Out For',         ch: '需留意之处' },
    // Wealth section — structured group headings (other Chinese copy is prompt-driven)
    wealthSources:       { en: 'How Wealth Comes to You',         ch: '财富来源' },
    wealthCapacity:      { en: 'Capacity to Build & Keep',        ch: '聚财守财能力' },
    wealthRisks:         { en: 'Wealth Risks & Leaks',            ch: '破财风险' },
    wealthTiming:        { en: 'Timing of Prosperity',            ch: '财运时机' },
    wealthStrategy:      { en: 'Wealth Strategy',                 ch: '理财建议' },
    // Family section — structured group headings (other Chinese copy is prompt-driven)
    familyRoots:         { en: 'Roots & Ancestry',               ch: '根源与祖辈' },
    familyParents:       { en: 'Your Parents',                   ch: '父母' },
    familySiblings:      { en: 'Siblings & Friends Growing Up',  ch: '手足与成长伙伴' },
    // Romance section — structured group headings (other Chinese copy is prompt-driven)
    romancePartner:      { en: 'How You Love & Who Suits You',   ch: '爱的方式与良配' },
    romanceSpouse:       { en: 'Your Spouse',                    ch: '配偶' },
    romanceJourney:      { en: 'The Journey & Its Timing',       ch: '情路与时机' },
    romanceChildren:     { en: 'Children & Your Own Home',       ch: '子女与家庭' },
    personalityProfile: { en: 'Personality Profile',             ch: '性格分析' },
    yourArchetype:    { en: 'Your Archetype:',                   ch: '命盘原型：' },
    elementLabel:     { en: 'Element:',                          ch: '五行：' },
    keyTraits:        { en: 'Key Traits:',                       ch: '核心特质：' },
    strengths:        { en: 'Strengths:',                        ch: '优势：' },
    areasToNote:      { en: 'Areas to Note:',                    ch: '注意事项：' },
    luckyColors:      { en: 'Lucky Colors:',                     ch: '幸运颜色：' },
    luckyNumbers:     { en: 'Lucky Numbers:',                    ch: '幸运数字：' },
    yourSummary:      { en: 'Your Summary',                      ch: '命盘总结' },
    lifeAspects:      { en: 'Life Aspects',                      ch: '人生面向' },
    lifeAspectsDesc:  { en: 'Key areas influenced by your Bazi chart', ch: '八字命盘影响的关键人生领域' },
    careerWealth:     { en: 'Career & Wealth',                   ch: '事业与财富' },
    careerWealthDesc: { en: 'Your {element} element suggests focusing on careers that align with your natural strengths. Lucky elements provide additional guidance for prosperity.',
                        ch: '您的{element}五行建议聚焦于与天赋契合的事业方向，用神五行为财富积累提供指引。' },
    relationships:    { en: 'Relationships',                     ch: '感情与婚姻' },
    relationshipsDesc:{ en: "The Day Pillar's earthly branch represents your spouse palace. Understanding this helps in relationship compatibility and harmony.",
                        ch: '日柱地支为配偶宫，深入了解有助于感情和谐与婚姻配合。' },
    healthWellness:   { en: 'Health & Wellness',                 ch: '健康养生' },
    healthWellnessDesc:{ en: 'Element imbalances can indicate areas of health to watch. Strengthening weak elements through lifestyle choices promotes wellbeing.',
                         ch: '五行失衡可能影响健康，通过生活方式强化弱势五行有助于养生保健。' },
    personalGrowth:   { en: 'Personal Growth',                   ch: '个人成长' },
    personalGrowthDesc:{ en: 'Your chart reveals natural talents and areas for development. Focus on cultivating your lucky elements for optimal growth.',
                         ch: '命盘揭示您的天赋与发展方向，专注培育用神五行有助于达到最佳成长状态。' },
    // Delete / misc
    deleteBtn:        { en: 'Delete',           ch: '删除' },
    deleteTitle:      { en: 'Delete Profile',   ch: '删除命盘' },
    deleteCancel:     { en: 'Cancel',           ch: '取消' },
    deleteOk:         { en: 'Delete',           ch: '删除' },
    // Inline feedback (errors only — success is communicated by the UI change itself)
    // "chart" not "profile": the ch side already said 命盘, and the rest of the app calls
    // it a chart.
    //
    // Names the delete ICON, not the Popconfirm's "Delete" button — deliberately.
    // handleDeleteProfile catches its own error and returns normally, so the confirm
    // popup has already CLOSED by the time this message renders; "Delete" is no longer
    // on screen. The real recourse is to click the trash icon again to reopen it.
    deleteError:      { en: 'We are not able to delete this chart. Please select the delete icon to try again.', ch: '无法删除此命盘，请再次点击删除图标重试。' },
    // Names the adjacent button (retryInsights) rather than saying "please retry".
    // "part of" is load-bearing: sections fail independently and the button re-requests
    // ONLY the failed ones, so this is never a full five-section regeneration.
    errorInsights:    { en: "We couldn't generate part of your reading. Please select Regenerate insights.",
                        ch: '部分解读暂时无法生成，请点击「重新生成解读」。' },
    retryInsights:    { en: 'Regenerate insights', ch: '重新生成解读' },
    profileNotFound:  { en: 'Profile not found', ch: '找不到命盘' },
    loadingProfile:   { en: 'Loading profile...', ch: '加载中...' },
    tdLabel:          { en: 'Coming Soon',      ch: '敬请期待' },
    male:             { en: 'Male',             ch: '男' },
    female:           { en: 'Female',           ch: '女' },
    // Pillar Interactions card
    pillarInteractions: { en: 'Pillar Interactions', ch: '柱位动态' },
    tier1Label:       { en: 'Structural',       ch: '纲领层' },
    tier2Label:       { en: 'Operational',      ch: '气势层' },
    tier3Label:       { en: 'Frictional',       ch: '琐碎层' },
    noInteractions:   { en: 'No pillar interactions found', ch: '无柱位互动' },
    // Day Master Strength card
    dayMasterStrength: { en: 'Day Master Strength', ch: '日主强弱' },
    dmSeasonalAuth:   { en: 'Season Strength',             ch: '得令' },
    dmRooting:        { en: 'Root Strength',              ch: '得地' },
    dmSupport:        { en: 'Stem Strength',              ch: '得势' },
    dmVerdictLabel:   { en: 'Verdict',              ch: '综合评判' },
  },
  sidebar: {
    profiles:         { en: 'Profiles',              ch: '命盘' },
    noProfiles:       { en: 'No profiles yet',        ch: '尚无命盘' },
    tools:            { en: 'Tools',                  ch: '工具' },
    compatibility:    { en: 'Compatibility',          ch: '合婚配对' },
    aiOracleChat:     { en: 'AI Oracle Chat',         ch: 'AI 神算问答' },
    guest:            { en: 'Guest',                  ch: '访客' },
    login:            { en: 'Login',                  ch: '登录' },
    deleteProfile:    { en: 'Delete Profile',         ch: '删除命盘' },
    deleteCancel:     { en: 'Cancel',                 ch: '取消' },
    deleteOk:         { en: 'Delete',                 ch: '删除' },
    modalTitle:       { en: 'Create New Bazi Profile', ch: '新建八字命盘' },
    solarTime:        { en: 'Solar Time',             ch: '真太阳时' },
    labelProfileName: { en: 'Profile Name',           ch: '姓名' },
    labelDob:         { en: 'Date of Birth',          ch: '出生日期' },
    labelTimeOfBirth: { en: 'Time of Birth',          ch: '出生时间' },
    labelGender:      { en: 'Gender',                 ch: '性别' },
    labelBirthLocation: { en: 'Birth Location',       ch: '出生地点' },
    labelLatitude:    { en: 'Latitude',               ch: '纬度' },
    labelLongitude:   { en: 'Longitude',              ch: '经度' },
    labelMale:        { en: 'Male',                   ch: '男' },
    labelFemale:      { en: 'Female',                 ch: '女' },
    btnGenerate:      { en: 'Generate My Bazi Chart', ch: '生成八字命盘' },
    errorGenerated:   { en: "We couldn't generate your chart at this time. Please try regenerating the chart.", ch: '暂时无法生成您的命盘，请重新生成命盘。' },
  },
  landing: {
    heroLine1:        { en: 'Timeless Insights,',    ch: '洞悉天机，' },
    heroLine2:        { en: 'Modern Foresight',       ch: '现代先见' },
    tagline:          { en: 'Rooted in ancient wisdom, driven by AI', ch: '根植古代智慧，AI 驱动' },
    formHeading:      { en: 'Initialize Your Reading', ch: '开始解读命盘' },
    formSubHeading:   { en: 'Provide your birth details to reveal your energetic signature.', ch: '输入出生资料，揭示您的命理签名。' },
    labelProfileName: { en: 'Profile Name',           ch: '姓名' },
    labelDob:         { en: 'Date of Birth',          ch: '出生日期' },
    labelTimeOfBirth: { en: 'Time of Birth',          ch: '出生时间' },
    labelGender:      { en: 'Gender',                 ch: '性别' },
    labelBirthLocation: { en: 'Birth Location',       ch: '出生地点' },
    labelMale:        { en: 'Male',                   ch: '男' },
    labelFemale:      { en: 'Female',                 ch: '女' },
    btnGenerate:      { en: 'Generate My Bazi Chart', ch: '生成我的八字命盘' },
    btnDemo:          { en: "Try Demo (Desmond's Profile)", ch: '试用示例（Desmond 命盘）' },
    newLabel:         { en: 'New?',                   ch: '初次使用？' },
    solarTime:        { en: 'Solar Time',             ch: '真太阳时' },
    featureAncientTitle: { en: 'Ancient Accuracy',   ch: '古典精准' },
    featureAncientDesc: { en: 'A repository of thousand-year-old manuscripts digitized into a precise logic engine. We maintain the original intent of the Imperial masters.',
                          ch: '千年古籍数字化，精准逻辑引擎，忠实还原帝师原意。' },
    featureAncientLabel: { en: 'Authentic Lineage',  ch: '正统传承' },
    featureFiveTitle: { en: 'Five Element Balance',   ch: '五行平衡' },
    featureFiveDesc:  { en: 'Visualize the distribution of Wood, Fire, Earth, Metal, and Water. Discover your flow and identify elemental deficiencies that shape your path.',
                        ch: '可视化木、火、土、金、水分布，发现您的流动，识别塑造您命途的五行缺失。' },
    featureFiveLabel: { en: 'Dynamic Equilibrium',   ch: '动态均衡' },
    featureLuckTitle: { en: 'Luck Pillars',           ch: '大运' },
    featureLuckDesc:  { en: 'Decipher the decade-long cycles of your life. Anticipate the changing tides of fortune to act when the cosmos is in your favor.',
                        ch: '解读人生十年大运周期，预见运势起伏，把握天时而动。' },
    featureLuckLabel: { en: 'Cyclical Foresight',     ch: '周期先见' },
  },
  form: {
    labelProfileName:   { en: 'Profile Name',           ch: '姓名' },
    labelDob:           { en: 'Date of Birth',          ch: '出生日期' },
    labelTimeOfBirth:   { en: 'Time of Birth',          ch: '出生时间' },
    labelGender:        { en: 'Gender',                 ch: '性别' },
    labelBirthLocation: { en: 'Birth Location',         ch: '出生地点' },
    labelMale:          { en: 'Male',                   ch: '男' },
    labelFemale:        { en: 'Female',                 ch: '女' },
    btnGenerate:        { en: 'Generate My Bazi Chart', ch: '生成八字命盘' },
    solarTime:          { en: 'Solar Time',             ch: '真太阳时' },
    // FALLBACK ONLY. When /api/chart answers, its own message (from lib/errors.ts
    // toClientError) is shown instead — it knows whether the failure was a timeout, an
    // outage or bad birth data. This covers the case where no response arrived at all.
    // Wording deliberately matches toClientError's 502 so the two read identically.
    errorGenerated:     { en: 'There is an error generating your chart. Please refresh the page and generate it again.', ch: '生成命盘时出现错误，请刷新页面后重新生成。' },
    // Fires in the brief window before anonymous sign-in completes. Names the submit
    // button (btnGenerate) as the retry, and says to wait — the condition is transient.
    notReady:           { en: 'Just a moment — we are getting things ready. Please select Generate My Bazi Chart again in a few seconds.', ch: '正在准备中，请稍候几秒后再次点击「生成八字命盘」。' },
    btnDemo:            { en: "Try Demo (Desmond's Profile)", ch: '试用示例（Desmond 命盘）' },
    newLabel:           { en: 'New?',                   ch: '初次使用？' },
  },
  element: {
    Wood:  { en: 'Wood',  ch: '木' },
    Fire:  { en: 'Fire',  ch: '火' },
    Earth: { en: 'Earth', ch: '土' },
    Metal: { en: 'Metal', ch: '金' },
    Water: { en: 'Water', ch: '水' },
  },
  // Error boundaries + 404. Its own namespace rather than an extension of `profile`
  // because app/error.tsx and app/not-found.tsx have nothing to do with profiles.
  //
  // Copy rules (same as lib/errors.ts, which handles the API-response side):
  //  - The TITLE names the artifact that failed ("Unable to load your chart"), never
  //    the event ("Something went wrong"). The user learns what broke from the
  //    headline alone, and the body is then free to carry only the action.
  //  - The BODY names its button by the exact visible label below, so copy and
  //    affordance cannot drift. Change a label -> change the body with it.
  //  - Never name infrastructure (no "service"/"backend"/"server").
  error: {
    chartTitle:    { en: 'Unable to load your chart', ch: '无法加载命盘' },
    // No positional word ("below"): ErrorState passes these to an antd Alert whose
    // action button renders INSIDE the alert on the right, not beneath it. Name the
    // action, never where it sits. (global-error.tsx does say "below" — there the
    // button really is beneath the text, in a plain flex column.)
    //
    // The chart boundary speaks in terms of the user's own action ("generate your chart
    // again" / Regenerate chart) rather than a generic retry: it is the more reassuring
    // and more concrete framing. Under the hood the button re-runs the page load, which
    // usually serves the chart straight from cache — but "regenerate" is the right
    // user-facing mental model, and the outcome is identical either way.
    chartBody:     { en: 'Please generate your chart again.', ch: '请重新生成您的命盘。' },
    // Chart-specific action label. Distinct from `retry` because ErrorState is shared
    // with the root boundary, where a page-level crash has no chart to regenerate.
    regenerateChart: { en: 'Regenerate chart',      ch: '重新生成命盘' },
    pageTitle:     { en: 'Unable to load this page', ch: '无法加载页面' },
    pageBody:      { en: 'Please select Try again.', ch: '请点击「重试」。' },
    // No notFound* strings: app/not-found.tsx redirects to '/' instead of rendering a
    // page, so there is nothing to translate. See that file for why.
    // Deliberately duplicates profile.retryInsights rather than sharing it — the copy
    // differs ('Try again' vs 'Retry') and the two controls must stay relabelable
    // independently.
    retry:         { en: 'Try again',               ch: '重试' },
    refId:         { en: 'Reference',               ch: '错误编号' },
  },
} as const;
