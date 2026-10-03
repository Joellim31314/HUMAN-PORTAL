import type {
  AgentNarrative,
  Area,
  BetSettlement,
  PersonaCluster,
  ProductAnswers,
  SimResult,
} from "@/lib/types"

export const LONDON_AREAS = [
  "Walthamstow",
  "Peckham",
  "Camden",
  "Stratford",
  "Shoreditch",
  "Clapham",
  "Kingston",
] as const

export const EXAMPLE_PRODUCT: ProductAnswers = {
  slug: "hojicha-bloom",
  name: "Hojicha Bloom",
  tagline: "Ready-to-drink roasted green tea — calm energy, no coffee jitters",
  category: "Beverages",
  price: "3.50",
  packSize: "330ml can",
  status: "prelaunch",
  channels: ["Cafés", "D2C online"],
  buyerGuess:
    "Health-conscious millennial professionals looking for a coffee alternative",
  choiceReason:
    "They choose it for calmer caffeine and antioxidants, without coffee bitterness",
  rejectReason: "",
  placementGuess: "shoreditch",
}

const CLUSTERS: Record<string, PersonaCluster> = {
  students: {
    name: "Matcha-switchers",
    share: 31,
    ages: "19–24",
    occupations: "Students, retail & hospitality workers",
    verdict: "adopt",
    drivers: ["social proof", "novelty", "identity"],
    adoptPct: 74,
    rejectPct: 9,
    ignorePct: 17,
  },
  creatives: {
    name: "Creative professionals",
    share: 27,
    ages: "25–34",
    occupations: "Designers, marketers, devs",
    verdict: "adopt",
    drivers: ["habit", "identity", "convenience"],
    adoptPct: 61,
    rejectPct: 16,
    ignorePct: 23,
  },
  wellness: {
    name: "Wellness parents",
    share: 24,
    ages: "30–42",
    occupations: "Parents, office workers",
    verdict: "ignore",
    drivers: ["price anchor", "trust", "habit"],
    adoptPct: 34,
    rejectPct: 28,
    ignorePct: 38,
  },
  loyalists: {
    name: "Coffee loyalists",
    share: 18,
    ages: "35–50",
    occupations: "Trades, drivers, managers",
    verdict: "reject",
    drivers: ["habit", "price anchor"],
    adoptPct: 12,
    rejectPct: 68,
    ignorePct: 20,
  },
}

export const AREAS: Area[] = [
  {
    slug: "walthamstow",
    name: "Walthamstow",
    borough: "E17",
    center: [51.5906, -0.0139],
    radiusM: 780,
    rank: 1,
    score: { trend: 92, gap: 85, shelf: 78, demo: 91, total: 87 },
    summary:
      "Trend heat is compounding (+320% QoQ on matcha-switcher content) with zero hojicha RTD stocked within 2km and a dense 24–35 creative + young-family base.",
    signals: [
      {
        id: "wal-1",
        platform: "TikTok",
        topic: "Matcha switching",
        quote:
          "stopped paying £5 for matcha lattes, making roasted tea at home instead — tastes like a hug",
        author: "londonmatchagirl",
        authorMeta: "24 · barista · E17",
        date: "2d ago",
        sentiment: "positive",
        confidence: "high",
      },
      {
        id: "wal-2",
        platform: "Reddit",
        topic: "Caffeine anxiety",
        quote:
          "r/london, where can I get actual hojicha? Not matcha, the roasted one. Tired of coffee jitters",
        author: "u/teaandcode",
        authorMeta: "27 · software dev",
        date: "5d ago",
        sentiment: "positive",
        confidence: "high",
      },
      {
        id: "wal-3",
        platform: "Reviews",
        topic: "Category whitespace",
        quote:
          "Closest match: Ito En Oi Ocha from the one Japanese grocer near the station — always sold out",
        author: "Google Maps review",
        authorMeta: "Tokyo Food Store, E17",
        date: "1w ago",
        sentiment: "mixed",
        confidence: "medium",
      },
      {
        id: "wal-4",
        platform: "TikTok",
        topic: "Local food scene",
        quote:
          "Walthamstow village is quietly the best food strip in London and nobody is talking about it",
        author: "eatsinlondon",
        authorMeta: "89k followers",
        date: "3d ago",
        sentiment: "positive",
        confidence: "medium",
      },
      {
        id: "wal-5",
        platform: "X",
        topic: "Price sensitivity",
        quote:
          "£3.50 for a can is fine if it's actually good. £5 matcha can get in the bin",
        author: "@e17foodie",
        authorMeta: "31 · local",
        date: "6d ago",
        sentiment: "mixed",
        confidence: "medium",
      },
    ],
    competitors: [
      {
        name: "Chi Forest / sparkling teas",
        note: "In 2 of 6 convenience stores; no roasted-tea variant",
      },
      {
        name: "Ito En Oi Ocha",
        note: "Single independent stockist, frequent stockouts",
      },
      {
        name: "Local matcha bar (open 2025)",
        note: "Queue at weekends — proves premium tea demand",
      },
    ],
    shelf: {
      outlets: 6,
      whitespace:
        "No RTD hojicha anywhere in E17; 4 of 6 outlets have an open chilled-tea facing gap",
    },
    demoFit: {
      matchPct: 91,
      note:
        "Cluster mix skews 24–35 creatives + students — matches the product's actual early signal base, not the assumed buyer",
    },
  },
  {
    slug: "peckham",
    name: "Peckham",
    borough: "SE15",
    center: [51.4743, -0.0696],
    radiusM: 720,
    rank: 2,
    score: { trend: 84, gap: 79, shelf: 70, demo: 81, total: 79 },
    summary:
      "Strong independent-retail culture and high trend affinity; slightly thinner physical whitespace than Walthamstow.",
    signals: [
      {
        id: "pec-1",
        platform: "TikTok",
        topic: "Matcha switching",
        quote: " Peckham Rye cafés need to stop sleepwalking on tea, I'd buy this weekly ",
        author: "peckhamfoodie",
        authorMeta: "26 · stylist",
        date: "1d ago",
        sentiment: "positive",
        confidence: "medium",
      },
      {
        id: "pec-2",
        platform: "Reddit",
        topic: "Caffeine anxiety",
        quote: "anyone else cut coffee and feel human again? what are you drinking instead",
        author: "u/ryeandshine",
        authorMeta: "29 · teacher",
        date: "4d ago",
        sentiment: "positive",
        confidence: "medium",
      },
      {
        id: "pec-3",
        platform: "Reviews",
        topic: "Category whitespace",
        quote: "Great coffee everywhere, but iced tea options are all sugar bombs",
        author: "Google Maps review",
        authorMeta: "Rye Lane convenience store",
        date: "2w ago",
        sentiment: "negative",
        confidence: "medium",
      },
    ],
    competitors: [
      { name: "Local cold-brew brands", note: "2 independent cafés bottle their own" },
      { name: "Arizona / Lipton RTD", note: "Present but ageing demographic" },
    ],
    shelf: {
      outlets: 5,
      whitespace: "2 of 5 outlets have gap in premium chilled tea",
    },
    demoFit: {
      matchPct: 81,
      note: "Young creative density high; slightly fewer students than E17",
    },
  },
  {
    slug: "camden",
    name: "Camden",
    borough: "NW1",
    center: [51.539, -0.1426],
    radiusM: 700,
    rank: 3,
    score: { trend: 76, gap: 64, shelf: 68, demo: 77, total: 71 },
    summary:
      "High footfall and tourist blend lift volume but dilute persona fit; healthy trend signal among 25–34 locals.",
    signals: [
      {
        id: "cam-1",
        platform: "TikTok",
        topic: "Matcha switching",
        quote: "Camden market stall idea: roasted tea flight. Would people get it?",
        author: "marketsellerlondon",
        authorMeta: "33 · trader",
        date: "3d ago",
        sentiment: "mixed",
        confidence: "medium",
      },
      {
        id: "cam-2",
        platform: "YouTube",
        topic: "Category education",
        quote: "Hojicha explained: why the 'boring' green tea is having a moment",
        author: "TeaTok",
        authorMeta: "210k views",
        date: "2w ago",
        sentiment: "positive",
        confidence: "high",
      },
      {
        id: "cam-3",
        platform: "Reviews",
        topic: "Price sensitivity",
        quote: "£3.80 near the lock, tourists pay it, locals walk to Sainsbury's",
        author: "Google Maps review",
        authorMeta: "Camden High St",
        date: "1w ago",
        sentiment: "mixed",
        confidence: "low",
      },
    ],
    competitors: [
      { name: "Boba & matcha chains", note: "4 within 1km — education done, but shelf rivalry" },
      { name: "Supermarket own-label teas", note: "Sainsbury's Local 300m away" },
    ],
    shelf: {
      outlets: 8,
      whitespace: "Premium chilled-tea facing present but contested",
    },
    demoFit: {
      matchPct: 77,
      note: "Local 25–34 fit strong; tourist share adds noise to signal",
    },
  },
  {
    slug: "stratford",
    name: "Stratford",
    borough: "E15",
    center: [51.5423, -0.0026],
    radiusM: 750,
    rank: 4,
    score: { trend: 66, gap: 70, shelf: 62, demo: 69, total: 67 },
    summary:
      "Westfield volume is tempting but chain-dominated; trend signal real yet concentrated around the student village.",
    signals: [
      {
        id: "str-1",
        platform: "Reddit",
        topic: "Caffeine anxiety",
        quote: "UEL library runs on energy drinks, some of us want off the ride",
        author: "u/stratfordstudent",
        authorMeta: "21 · student",
        date: "2d ago",
        sentiment: "positive",
        confidence: "medium",
      },
      {
        id: "str-2",
        platform: "TikTok",
        topic: "Convenience missions",
        quote: "Westfield meal deal review part 9 — the drinks fridge is a desert",
        author: "stratfordspends",
        authorMeta: "18k followers",
        date: "5d ago",
        sentiment: "negative",
        confidence: "medium",
      },
    ],
    competitors: [
      { name: "Westfield food hall brands", note: "Chains own the premium drinks space" },
      { name: "Pret / Itsu chilled teas", note: "Convenience default for office workers" },
    ],
    shelf: {
      outlets: 7,
      whitespace: "Chain facings locked; independents near the station are the opening",
    },
    demoFit: {
      matchPct: 69,
      note: "Student cluster present but thinner; office missions dominate",
    },
  },
  {
    slug: "shoreditch",
    name: "Shoreditch",
    borough: "E2",
    center: [51.5246, -0.0832],
    radiusM: 650,
    rank: 5,
    score: { trend: 58, gap: 38, shelf: 55, demo: 74, total: 56 },
    summary:
      "The obvious pick — and the trap: 11 direct competitors within 1km, cooling trend (-18% QoQ), premium fatigue in comments.",
    signals: [
      {
        id: "sho-1",
        platform: "TikTok",
        topic: "Premium fatigue",
        quote: "another £6 'artisan' tea latte in Shoreditch... we get it, you roasted the leaves",
        author: "londonfoodtruth",
        authorMeta: "134k followers",
        date: "1d ago",
        sentiment: "negative",
        confidence: "high",
      },
      {
        id: "sho-2",
        platform: "Reddit",
        topic: "Saturation",
        quote: "matcha places in E2 ranked — we counted 11. ELEVEN",
        author: "u/e2resident",
        authorMeta: "28 · designer",
        date: "1w ago",
        sentiment: "negative",
        confidence: "high",
      },
      {
        id: "sho-3",
        platform: "Reviews",
        topic: "Rent pressure",
        quote: "Great spot but £14k/m2 rent means everything here costs £6+",
        author: "Google Maps review",
        authorMeta: "Curtain Rd",
        date: "3w ago",
        sentiment: "negative",
        confidence: "medium",
      },
    ],
    competitors: [
      { name: "11 matcha/boba competitors", note: "Within 1km — direct shelf rivalry" },
      { name: "Blank Street / artisan cafés", note: "Own the premium RTD cooler" },
    ],
    shelf: {
      outlets: 9,
      whitespace: "No physical gap; the whitespace is the story we tell elsewhere",
    },
    demoFit: {
      matchPct: 74,
      note: "Persona fit is real — that's exactly why it's saturated",
    },
  },
  {
    slug: "clapham",
    name: "Clapham",
    borough: "SW4",
    center: [51.4651, -0.1402],
    radiusM: 700,
    rank: 6,
    score: { trend: 54, gap: 58, shelf: 50, demo: 62, total: 56 },
    summary:
      "Solid wellness-parent demographics but weak trend velocity; category education still needed here.",
    signals: [
      {
        id: "cla-1",
        platform: "TikTok",
        topic: "Wellness missions",
        quote: "Clapham mums trying to quit Diet Coke, day 3 — send alternatives",
        author: "claphammums",
        authorMeta: "8k followers",
        date: "4d ago",
        sentiment: "mixed",
        confidence: "low",
      },
      {
        id: "cla-2",
        platform: "Reddit",
        topic: "Category education",
        quote: "what even is hojicha, is it just burnt matcha?",
        author: "u/southlondonlife",
        authorMeta: "35 · office manager",
        date: "6d ago",
        sentiment: "mixed",
        confidence: "medium",
      },
    ],
    competitors: [
      { name: "Kombucha & kefir brands", note: "Own the gut-health fridge" },
      { name: "Supermarket iced teas", note: "Sugar-led range, no roasted tea" },
    ],
    shelf: {
      outlets: 6,
      whitespace: "Moderate; education budget needed before shelf pays off",
    },
    demoFit: {
      matchPct: 62,
      note: "Wellness parents over-index — the product's weakest cluster",
    },
  },
  {
    slug: "kingston",
    name: "Kingston",
    borough: "KT1",
    center: [51.4123, -0.3007],
    radiusM: 800,
    rank: 7,
    score: { trend: 38, gap: 46, shelf: 42, demo: 44, total: 42 },
    summary:
      "Lowest trend affinity and thinnest persona match; strong supermarket presence means head-on own-label competition.",
    signals: [
      {
        id: "kin-1",
        platform: "X",
        topic: "Category apathy",
        quote: "Kingston has two bubble tea shops and both are empty on weekdays",
        author: "@kingstonlocal",
        authorMeta: "local account",
        date: "1w ago",
        sentiment: "negative",
        confidence: "medium",
      },
      {
        id: "kin-2",
        platform: "Reviews",
        topic: "Own-label pressure",
        quote: "Tesco own iced tea £1.80 — hard to argue with",
        author: "Google Maps review",
        authorMeta: "Kingston Tesco Extra",
        date: "2w ago",
        sentiment: "negative",
        confidence: "medium",
      },
    ],
    competitors: [
      { name: "Tesco/Sainsbury's own-label", note: "Price anchor £1.80 vs your £3.50" },
      { name: "Bubble tea chains", note: "Underused — weak category signal" },
    ],
    shelf: {
      outlets: 5,
      whitespace: "None meaningful; big-box dominates",
    },
    demoFit: {
      matchPct: 44,
      note: "Older, family-led mix; all four clusters under-index",
    },
  },
]

function heroNarratives(areaSlug: string): AgentNarrative[] {
  const bank: Record<string, AgentNarrative[]> = {
    walthamstow: [
      {
        name: "Maya",
        age: 22,
        job: "student & weekend barista",
        cluster: "Matcha-switchers",
        verdict: "adopt",
        text: "Maya sees the can at the Tokyo Food Store till — the same shelf where Oi Ocha is always sold out. £3.50 is fine; she pays more for matcha. She posts it within the hour. Her gym group chat has asked about it twice this week.",
      },
      {
        name: "Dan",
        age: 28,
        job: "graphic designer",
        cluster: "Creative professionals",
        verdict: "adopt",
        text: "Dan quit coffee in January after the jitters got embarrassing in client calls. He's the 'calm energy' buyer verbatim — but he will only trust it after one person he rates posts it. Second sighting = purchase.",
      },
      {
        name: "Graham",
        age: 46,
        job: "self-employed electrician",
        cluster: "Coffee loyalists",
        verdict: "reject",
        text: "Graham tried one because his daughter left it in the van. 'Tastes like weak tea that's given up.' Habit wins: he's bought the same Costa flat white every morning for nine years. Price isn't the objection — routine is.",
      },
    ],
    peckham: [
      {
        name: "Amara",
        age: 25,
        job: "junior architect",
        cluster: "Creative professionals",
        verdict: "adopt",
        text: "Amara buys it from the café that bottles its own cold brew — she trusts their shelf. The roasted, less-bitter pitch lands exactly; she's been quietly dropping coffee since Ramadan.",
      },
      {
        name: "Josh",
        age: 21,
        job: "barista",
        cluster: "Matcha-switchers",
        verdict: "adopt",
        text: "Josh will champion it at work if the café stocks it — but he wants the café's margin story first. Social proof flows through him, not through ads.",
      },
    ],
    shoreditch: [
      {
        name: "Lena",
        age: 29,
        job: "brand strategist",
        cluster: "Creative professionals",
        verdict: "ignore",
        text: "Lena's seen four 'new tea' launches this quarter. Without a friend vouching for it, it's wallpaper. The £3.50 price is right — the neighbourhood is just deaf to another artisan launch.",
      },
      {
        name: "Theo",
        age: 34,
        job: "product manager",
        cluster: "Coffee loyalists",
        verdict: "reject",
        text: "Theo calculates cost per mg of caffeine and leaves. He's also still annoyed about the matcha place that replaced his sandwich shop.",
      },
    ],
  }
  return bank[areaSlug] ?? []
}

function fallbackNarratives(
  areaName: string,
  verdict: "adopt" | "reject" | "ignore"
): AgentNarrative[] {
  const names = ["Priya", "Sam", "Jordan", "Fatima"]
  return Object.values(CLUSTERS)
    .filter((c) => c.verdict === verdict)
    .map((c, i) => ({
      name: names[i % names.length],
      age: parseInt(c.ages) || 29,
      job: c.occupations.split(",")[0].toLowerCase(),
      cluster: c.name,
      verdict: c.verdict,
      text: `${c.name} in ${areaName}: the ${c.drivers.join(" + ")} drivers ${c.verdict === "adopt" ? "line up with what this area's signals already show" : c.verdict === "reject" ? "work against the product here, consistent with the area's weaker scores" : "don't move them either way here"}.`,
    }))
}

export const SIM_RESULTS: Record<string, SimResult> = Object.fromEntries(
  AREAS.map((area) => {
    const overall =
      area.slug === "walthamstow"
        ? { adopt: 62, reject: 18, ignore: 20 }
        : area.slug === "peckham"
          ? { adopt: 55, reject: 22, ignore: 23 }
          : area.slug === "camden"
            ? { adopt: 48, reject: 28, ignore: 24 }
            : area.slug === "stratford"
              ? { adopt: 44, reject: 30, ignore: 26 }
              : area.slug === "shoreditch"
                ? { adopt: 31, reject: 47, ignore: 22 }
                : area.slug === "clapham"
                  ? { adopt: 38, reject: 33, ignore: 29 }
                  : { adopt: 26, reject: 44, ignore: 30 }

    const heroes = heroNarratives(area.slug)
    const topVerdict: "adopt" | "reject" | "ignore" =
      overall.adopt >= overall.reject && overall.adopt >= overall.ignore
        ? "adopt"
        : overall.reject >= overall.ignore
          ? "reject"
          : "ignore"
    const all = [
      ...heroes,
      ...fallbackNarratives(area.name, topVerdict),
    ].slice(0, Object.keys(CLUSTERS).length + 1)

    const takeaway =
      area.slug === "walthamstow"
        ? "Lead here. Win the matcha-switchers through the Tokyo Food Store and one gym-adjacent café; the 'calm energy' story is already believed in E17."
        : area.slug === "shoreditch"
          ? "Do not lead here. Persona fit is real but the shelf war is lost and the neighbourhood is premium-fatigued — revisit only after two proof-posts from other areas."
          : area.slug === "kingston"
            ? "Avoid for launch. Own-label price anchoring plus weak trend affinity makes this an education spend, not a launch market."
            : `${area.name} is a ${overall.adopt >= 44 ? "credible second wave" : "watchlist"} market: ${overall.adopt}% modelled adoption, contingent on ${area.slug === "peckham" ? "winning the independent cafés first" : area.slug === "camden" ? "siting away from the tourist strip" : "the student-village convenience stores"}.`

    return [
      area.slug,
      {
        areaSlug: area.slug,
        heroNarratives: heroes.length > 0 ? heroes : all.slice(0, 3),
        allNarratives: all,
        clusters: Object.values(CLUSTERS),
        overall,
        takeaway,
      } satisfies SimResult,
    ]
  })
)

export function getSettlements(product: ProductAnswers): BetSettlement[] {
  const placementArea = AREAS.find((a) => a.slug === product.placementGuess)
  const top = AREAS[0]
  return [
    {
      key: "placement",
      label: "Placement",
      userSaid: placementArea?.name ?? product.placementGuess,
      signalsSay: `Signals say ${top.name} — it scores ${
        top.score.total - (placementArea?.score.total ?? 0)
      } points higher, with stronger shelf whitespace and fresher trend heat.`,
      status:
        product.placementGuess === top.slug
          ? ("confirmed" as const)
          : ("contradicted" as const),
      areaSlug: placementArea?.slug,
    },
    {
      key: "buyer",
      label: "Buyer",
      userSaid: product.buyerGuess,
      signalsSay:
        "The loudest signals come from 19–34 matcha-switchers and creative workers. 'Wellness millennial professionals' exist in the data — but they're the quiet third, not the engine.",
      status: "contradicted" as const,
    },
    {
      key: "choice",
      label: "Why they choose it",
      userSaid: product.choiceReason,
      signalsSay:
        "Confirmed almost word-for-word: 'calm energy', 'no jitters', 'coffee alternative' are the exact phrases repeating across TikTok and Reddit.",
      status: "confirmed" as const,
    },
  ]
}
