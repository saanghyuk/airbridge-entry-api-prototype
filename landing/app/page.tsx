"use client";

import Image from "next/image";
import { useState } from "react";

/* ── Nav ─────────────────────────────────────────────── */
function Nav() {
  const [open, setOpen] = useState(false);
  return (
    <nav className="fixed top-0 w-full z-50 bg-[#050510]/70 backdrop-blur-2xl border-b border-white/[0.08]">
      <div className="max-w-7xl mx-auto px-6 md:px-8 h-16 md:h-18 flex items-center justify-between">
        <Image src="/airbridge-logo.png" alt="Airbridge" width={120} height={28} style={{width:'auto',height:'auto'}} priority />
        {/* Desktop */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm text-white/55 hover:text-white transition-colors">Features</a>
          <a href="#proof" className="text-sm text-white/55 hover:text-white transition-colors">Results</a>
          <a href="#how" className="text-sm text-white/55 hover:text-white transition-colors">How It Works</a>
          <a href="#demo" className="text-sm text-white/55 hover:text-white transition-colors">Live Demo</a>
          <a href="#contact" className="btn-primary text-white text-sm px-6 py-2.5 rounded-full font-medium">Get Started</a>
        </div>
        {/* Mobile hamburger */}
        <button onClick={() => setOpen(!open)} className="md:hidden text-white/60 p-2">
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2"><path d={open ? "M6 6l12 12M6 18L18 6" : "M4 7h16M4 12h16M4 17h16"} /></svg>
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-white/[0.08] bg-[#050510]/95 backdrop-blur-2xl px-6 py-4 space-y-3">
          {[["#features","Features"],["#proof","Results"],["#how","How It Works"],["#demo","Live Demo"]].map(([h,l])=>(
            <a key={h} href={h} onClick={()=>setOpen(false)} className="block text-white/60 hover:text-white py-2">{l}</a>
          ))}
          <a href="#start" onClick={()=>setOpen(false)} className="btn-primary block text-center text-white px-6 py-3 rounded-full font-medium mt-2">Get Started</a>
        </div>
      )}
    </nav>
  );
}

/* ── Hero ────────────────────────────────────────────── */
function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center text-center px-6 overflow-hidden pt-20">
      <div className="aurora" />
      <div className="absolute inset-0 grid-pattern opacity-40" />
      <div className="relative z-10 max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#0062FA]/30 bg-[#0062FA]/5 mb-8 md:mb-10">
          <span className="w-2 h-2 rounded-full bg-[#0062FA] animate-pulse" />
          <span className="text-xs md:text-sm text-[#3d8bff] font-medium">Airbridge Entry API</span>
        </div>
        <h1 className="text-3xl sm:text-[2.5rem] md:text-[3.5rem] font-extrabold tracking-tight leading-[1.08] mb-6 md:mb-8">
          Your users leave<br />
          <span className="gradient-text">before your product</span><br />
          even gets a chance.
        </h1>
        <p className="text-base md:text-xl text-white/55 max-w-2xl mx-auto mb-10 md:mb-14 leading-relaxed px-2">
          You spend $2-5 to bring each user. 77% never come back.
          Every personalization tool needs history they haven&apos;t created yet.
          <br /><br />
          <span className="text-white/80 font-medium">Airbridge predicts who they are &mdash; in the first 5 minutes &mdash; using data no one else has.</span>
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 md:gap-4">
          <a href="#demo" className="btn-primary text-white px-8 md:px-10 py-3.5 md:py-4 rounded-full font-semibold text-base md:text-lg w-full sm:w-auto text-center">
            Try the Live API &rarr;
          </a>
          <a href="#proof" className="btn-ghost text-white/50 px-8 md:px-10 py-3.5 md:py-4 rounded-full font-semibold text-base md:text-lg hover:text-white w-full sm:w-auto text-center">
            See the Numbers &darr;
          </a>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[#050510] to-transparent" />
    </section>
  );
}

/* ── Problem ─────────────────────────────────────────── */
function Problem() {
  return (
    <section className="pt-20 md:pt-28 pb-10 md:pb-16 px-6 relative">
      <div className="absolute inset-0 glow-blue opacity-20" />
      <div className="relative z-10 max-w-5xl mx-auto text-center">
        <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-6">The Problem</p>
        <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight mb-12 md:mb-20">
          The first <span className="gradient-text">5 minutes</span> decide everything.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-12 md:mb-20">
          {[
            { num: "$2–5", label: "average CPI to acquire one user" },
            { num: "77%", label: "of users never return after Day 1*" },
            { num: "$0", label: "invested in their first experience" },
          ].map((item, i) => (
            <div key={i} className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10">
              <p className="text-4xl md:text-6xl font-black gradient-text-warm mb-2 md:mb-4">{item.num}</p>
              <p className="text-white/55 text-sm md:text-lg">{item.label}</p>
            </div>
          ))}
        </div>
        <p className="text-xl md:text-2xl font-bold mb-4 md:mb-6">
          Airbridge Entry API: personalize <span className="text-[#3d8bff]">from the very first screen.</span>
        </p>
        <p className="text-base md:text-lg text-white/55">
          One API call, 5 minutes after app open &mdash; 4 real-time predictions.
        </p>
      </div>
    </section>
  );
}

/* ── How Is This Possible ────────────────────────────── */
function HowPossible() {
  return (
    <section className="pt-4 md:pt-8 pb-12 md:pb-16 px-6 relative">
      <div className="absolute inset-0 glow-blue opacity-20" />
      <div className="relative z-10 max-w-5xl mx-auto">
        <div className="text-center mb-8 md:mb-12">
          <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">The Secret</p>
          <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight">
            How do you predict a user<br /><span className="gradient-text">with zero history?</span>
          </h2>
        </div>

        <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10 mb-6">
          <p className="text-lg md:text-2xl font-bold mb-6 text-center">
            Their history doesn&apos;t start at install. It starts at the <span className="text-[#3d8bff]">first ad impression.</span>
          </p>
          <p className="text-white/55 text-center leading-relaxed max-w-3xl mx-auto mb-10">
            Before a user ever opens your app, they&apos;ve already left a trail: which channels they came from, how many ads they saw, whether they clicked or just scrolled past, how long they hesitated before installing. Google, Meta, and TikTok each poured billions into ML-powered targeting — and the result of that optimization is recorded in the <strong className="text-white/60">multi-touchpoint ad journey</strong>.
          </p>

          {/* Visual: journey timeline */}
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-2 md:gap-3 overflow-x-auto pb-4">
              {[
                { label: "Meta Ad", type: "Impression", color: "bg-blue-500/40 text-blue-200" },
                { label: "Google Ad", type: "Click", color: "bg-emerald-500/40 text-emerald-200" },
                { label: "TikTok Ad", type: "View", color: "bg-pink-500/40 text-pink-200" },
                { label: "Google Ad", type: "Click", color: "bg-emerald-500/40 text-emerald-200" },
                { label: "Install + Open", type: "✓", color: "bg-[#0062FA] text-white font-bold" },
                { label: "After 5 min", type: "Ready!", color: "bg-amber-500/80 text-white font-bold" },
                { label: "API Call", type: "→ 4 Predictions", color: "bg-white text-black font-bold" },
              ].map((step, i) => (
                <div key={i} className="flex items-center shrink-0">
                  <div className={`${step.color} rounded-xl px-3 py-2 text-center`}>
                    <p className="text-xs font-semibold whitespace-nowrap">{step.label}</p>
                    {step.type && <p className="text-[10px] opacity-60">{step.type}</p>}
                  </div>
                  {i < 6 && <svg className="w-4 h-4 text-white/10 shrink-0 mx-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" /></svg>}
                </div>
              ))}
            </div>
          </div>

          <p className="text-center text-white/55 text-sm mt-6">
            Every touchpoint is a signal. The platforms&apos; billion-dollar ML optimization already sorted your users &mdash; we just read the result.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-8">
            <h3 className="text-lg font-bold mb-3">Dozens of signals from the ad journey</h3>
            <p className="text-sm text-white/55 mb-4">Which channels, how many touches, click vs impression ratio, how long they hesitated, how urgently they came back — the DNA of user intent, extracted from billions of dollars of ad platform ML.</p>
            <div className="flex flex-wrap gap-2">
              {["Channel mix", "Touch frequency", "Click vs impression", "Time to install", "Recency pressure", "Channel entropy", "DA/SA split", "Touch velocity", "and dozens more..."].map(t => (
                <span key={t} className="text-xs px-2.5 py-1 rounded-full bg-[#0062FA]/10 text-[#3d8bff]">{t}</span>
              ))}
            </div>
          </div>
          <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-8">
            <h3 className="text-lg font-bold mb-3">Every micro-action in the first 5 minutes</h3>
            <p className="text-sm text-white/55 mb-4">Did they browse? Sign in? Add to cart? Every micro-action in the first 300 seconds tells us exactly where they are in the purchase funnel.</p>
            <div className="flex flex-wrap gap-2">
              {["Product views", "Sign-in", "Add to cart", "Wishlist", "Home browse", "Sign-up", "Deeplink", "Onboarding", "and more..."].map(t => (
                <span key={t} className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300">{t}</span>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center mt-8 text-lg text-white/40">
          <strong className="text-white">70+ raw signals distilled into 25 precision features.</strong> The ad journey reveals <em>who this person is</em> — their intent, urgency, and value. The in-app behavior reveals <em>what they want right now</em>.
          <br /><br />No other platform on earth has both. <span className="text-[#3d8bff] font-semibold">Only Airbridge, the MMP, has this data.</span>
        </p>
      </div>
    </section>
  );
}

/* ── Features ────────────────────────────────────────── */
function Features() {
  const cards = [
    { icon: <svg className="w-8 h-8 md:w-10 md:h-10 text-[#3d8bff]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.308 48.308 0 0 0 5.887-.515c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" /></svg>, title: "Optimal Message Type", desc: "Which psychological trigger works best? Discount, social proof, scarcity, or novelty. Learned from causal experiments, not guesses.", json: '"best_trigger": "price_appeal"', accent: "from-[#0062FA]/10 to-transparent" },
    { icon: <svg className="w-8 h-8 md:w-10 md:h-10 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>, title: "3-Day Purchase Probability", desc: "Know who will convert. Focus your budget on high-intent users. Save it for everyone else.", json: '"d3_purchase_prob": 0.87', accent: "from-emerald-500/10 to-transparent" },
    { icon: <svg className="w-8 h-8 md:w-10 md:h-10 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" /></svg>, title: "3-Day Churn Risk", desc: "This user is about to leave forever. You have one shot. The API tells you who and what message to use.", json: '"d3_churn_prob": 0.72', accent: "from-rose-500/10 to-transparent" },
    { icon: <svg className="w-8 h-8 md:w-10 md:h-10 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" /></svg>, title: "30-Day Predicted LTV", desc: "Is this a $500 customer or a $2 customer? VIP coupon for high-value, basic welcome for low.", json: '"pltv": { "tier": "high", "percentile": 92, "tier_avg_ltv": 110000 }', accent: "from-amber-500/10 to-transparent" },
  ];
  return (
    <section id="features" className="py-12 md:py-20 px-6 relative">
      <div className="section-divider max-w-5xl mx-auto mb-8 md:mb-16" />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8 md:mb-12">
          <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">What You Get</p>
          <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight">4 predictions. <span className="gradient-text">One JSON.</span></h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          {cards.map((c, i) => (
            <div key={i} className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10 relative overflow-hidden group">
              <div className={`absolute top-0 left-0 right-0 h-40 bg-gradient-to-b ${c.accent} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              <div className="relative z-10">
                <div className="mb-4 md:mb-6">{c.icon}</div>
                <h3 className="text-xl md:text-2xl font-bold mb-2 md:mb-3">{c.title}</h3>
                <p className="text-white/55 mb-4 md:mb-6 leading-relaxed text-sm md:text-base">{c.desc}</p>
                <code className="text-xs md:text-sm text-[#3d8bff] bg-black/40 px-3 md:px-4 py-1.5 md:py-2 rounded-lg md:rounded-xl inline-block border border-white/5">{c.json}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Proof — Visual ──────────────────────────────────── */
function Proof() {
  return (
    <section id="proof" className="py-12 md:py-20 px-6 relative">
      <div className="aurora" />
      <div className="relative z-10 max-w-5xl mx-auto">
        <div className="text-center mb-8 md:mb-12">
          <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">Proven Results</p>
          <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight">Not a pitch. <span className="gradient-text">Real data.</span></h2>
          <p className="text-white/55 text-base md:text-lg mt-4">From actual mobile apps, not simulations.</p>
        </div>

        {/* Purchase Prediction — bar comparison */}
        <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10 mb-4 md:mb-6">
          <h3 className="text-lg md:text-xl font-bold mb-1">Purchase Prediction</h3>
          <p className="text-xs md:text-sm text-white/55 mb-6 md:mb-8">Model ranks users by purchase likelihood. Top 10% vs Bottom 10% actual purchase rate.</p>
          <div className="space-y-4 md:space-y-5">
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-xs md:text-sm text-white/40">Top 10% predicted</span>
                <span className="text-xl md:text-2xl font-black text-white">94.7%</span>
              </div>
              <div className="h-8 md:h-10 bg-white/[0.03] rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-[#0062FA] to-[#3d8bff]" style={{width:'94.7%'}} />
              </div>
            </div>
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-xs md:text-sm text-white/40">Bottom 10% predicted</span>
                <span className="text-xl md:text-2xl font-black text-white/40">0.6%</span>
              </div>
              <div className="h-8 md:h-10 bg-white/[0.03] rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-white/10" style={{width:'2%'}} />
              </div>
            </div>
          </div>
          <div className="mt-6 md:mt-8 pt-4 md:pt-6 border-t border-white/[0.08] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <p className="text-sm text-white/30">When the model says &ldquo;this user will buy&rdquo; &mdash; they actually buy.</p>
            <span className="text-xl md:text-2xl font-black gradient-text">154&times; difference</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          {/* Churn Prediction */}
          <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10">
            <h3 className="text-lg md:text-xl font-bold mb-1">Churn Prediction</h3>
            <p className="text-xs md:text-sm text-white/55 mb-6 md:mb-8">Top 10% churn-risk users: actual churn rate</p>
            <div className="flex items-center gap-6 md:gap-8">
              <div className="relative w-20 h-20 md:w-24 md:h-24 shrink-0">
                <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="10" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="url(#churnGrad)" strokeWidth="10"
                    strokeDasharray={`${81.2 * 2.51} ${100 * 2.51}`} strokeLinecap="round" />
                  <defs><linearGradient id="churnGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#f43f5e" /><stop offset="100%" stopColor="#fb923c" /></linearGradient></defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg md:text-xl font-black text-white">81.2%</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-white/55 leading-relaxed">
                  Of users the model flagged as &ldquo;will churn&rdquo;, <span className="text-white font-semibold">81.2% actually left</span> within 3 days.
                </p>
                <p className="text-xs text-white/35 mt-2">Bottom 10%: only 11.9% churned.</p>
              </div>
            </div>
          </div>

          {/* LTV Separation */}
          <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10">
            <h3 className="text-lg md:text-xl font-bold mb-1">LTV Tier Separation</h3>
            <p className="text-xs md:text-sm text-white/55 mb-6 md:mb-8">Average 30-day revenue by predicted tier</p>
            <div className="space-y-3 md:space-y-4">
              {[
                { tier: "High", value: "₩110,000", w: "100%", color: "from-amber-500 to-amber-600" },
                { tier: "Medium", value: "₩9,300", w: "8.5%", color: "from-[#0062FA] to-[#3d8bff]" },
                { tier: "Low", value: "₩250", w: "0.5%", color: "from-white/20 to-white/10" },
              ].map((t) => (
                <div key={t.tier}>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs md:text-sm text-white/40">{t.tier} tier</span>
                    <span className="text-sm md:text-base font-bold text-white">{t.value}</span>
                  </div>
                  <div className="h-5 md:h-6 bg-white/[0.03] rounded-full overflow-hidden">
                    <div className={`h-full rounded-full bg-gradient-to-r ${t.color}`} style={{width: t.w, minWidth: '8px'}} />
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4 md:mt-6 pt-3 md:pt-4 border-t border-white/[0.08] text-right">
              <span className="text-xl md:text-2xl font-black gradient-text">440&times; difference</span>
            </p>
          </div>
        </div>

        {/* Bottom stat bar */}
        <div className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-8 mt-4 md:mt-6 flex flex-col sm:flex-row items-center justify-around gap-6 md:gap-4 text-center">
          <div>
            <p className="text-2xl md:text-3xl font-black stat-number">&lt;200ms</p>
            <p className="text-xs md:text-sm text-white/55 mt-1">API response time</p>
          </div>
          <div className="hidden sm:block w-px h-12 bg-white/[0.06]" />
          <div>
            <p className="text-2xl md:text-3xl font-black stat-number">5 min</p>
            <p className="text-xs md:text-sm text-white/55 mt-1">after app open</p>
          </div>
          <div className="hidden sm:block w-px h-12 bg-white/[0.06]" />
          <div>
            <p className="text-2xl md:text-3xl font-black stat-number">25</p>
            <p className="text-xs md:text-sm text-white/55 mt-1">features analyzed</p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Why Airbridge ───────────────────────────────────── */
function WhyAirbridge() {
  // reduced spacing
  const rows = [
    { data: "Device info (OS, model)", accuracy: "Almost none", who: "Anyone", hl: false },
    { data: "Multi-touch ad journey", accuracy: "High", who: "Only Airbridge", hl: true },
    { data: "First 5-min in-app behavior", accuracy: "High", who: "Any SDK app", hl: false },
    { data: "Ad journey + In-app combined", accuracy: "Unmatched", who: "Only Airbridge (the MMP) — no substitute", hl: true },
  ];
  return (
    <section className="py-12 md:py-20 px-6 relative">
      <div className="section-divider max-w-5xl mx-auto mb-8 md:mb-16" />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10 md:mb-16">
          <p className="text-sm font-semibold text-orange-400 tracking-widest uppercase mb-4">Why Us</p>
          <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight">
            Every other tool <span className="gradient-text-warm">gives up</span> on new users.
          </h2>
          <p className="text-white/55 text-base md:text-lg mt-4 max-w-2xl mx-auto">
            No one can predict new users — unless you have the data they generated <em>before</em> installing.
          </p>
          <div className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-[#0062FA]/30 bg-[#0062FA]/5">
            <span className="text-sm md:text-base text-[#3d8bff] font-semibold">There is no alternative. Only Airbridge — as the MMP — has the multi-touchpoint ad journey.<br />No one else can replicate this.</span>
          </div>
        </div>
        {/* Mobile: cards instead of table */}
        <div className="hidden md:block card-glass rounded-3xl overflow-hidden">
          <table className="w-full">
            <thead><tr className="border-b border-white/[0.10]">
              <th className="text-left p-6 text-sm font-medium text-white/40">Data Source</th>
              <th className="text-left p-6 text-sm font-medium text-white/40">Prediction Power</th>
              <th className="text-left p-6 text-sm font-medium text-white/40">Who Has It</th>
            </tr></thead>
            <tbody>{rows.map((r, i) => (
              <tr key={i} className={`border-b border-white/[0.10] ${r.hl ? "row-highlight" : ""}`}>
                <td className="p-6 text-white/60">{r.data}</td>
                <td className="p-6"><span className={r.hl ? "font-bold text-[#3d8bff]" : "text-white/40"}>{r.accuracy}</span></td>
                <td className="p-6">{r.hl ? (
                  <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0062FA]/10 text-[#3d8bff] text-sm font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#0062FA]" />{r.who}
                  </span>) : <span className="text-white/40">{r.who}</span>}
                </td>
              </tr>))}
            </tbody>
          </table>
        </div>
        {/* Mobile cards */}
        <div className="md:hidden space-y-3">
          {rows.map((r, i) => (
            <div key={i} className={`card-glass rounded-2xl p-5 ${r.hl ? "border-[#0062FA]/20" : ""}`}>
              <p className="text-white/60 text-sm mb-2">{r.data}</p>
              <div className="flex justify-between items-center">
                <span className={r.hl ? "font-bold text-[#3d8bff]" : "text-white/40"}>{r.accuracy}</span>
                {r.hl ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0062FA]/10 text-[#3d8bff] text-xs font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#0062FA]" />{r.who}
                  </span>) : <span className="text-white/55 text-sm">{r.who}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── How It Works ────────────────────────────────────── */
function HowItWorks() {
  const steps = [
    { num: "01", week: "Week 1–2", title: "Exploration", desc: "Every new user gets a random message type. A real RCT builds the causal dataset.", badge: "RCT", color: "text-white bg-[#0062FA]/80" },
    { num: "02", week: "Week 3+", title: "Optimization", desc: "Causal ML learns the best message per user. 80% optimal, 20% random for continuous learning.", badge: "Causal ML", color: "text-white bg-purple-500/70" },
    { num: "03", week: "Ongoing", title: "Gets Smarter Every Week", desc: "Weekly retraining. Sharper predictions. Your app code never changes.", badge: "Auto", color: "text-white bg-emerald-500/70" },
  ];
  return (
    <section id="how" className="py-12 md:py-20 px-6 relative">
      <div className="absolute inset-0 glow-blue opacity-20" />
      <div className="relative z-10 max-w-4xl mx-auto">
        <div className="text-center mb-10 md:mb-16">
          <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">The Process</p>
          <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight">
            From zero data to<br /><span className="gradient-text">personalized experience.</span>
          </h2>
        </div>
        <div className="space-y-4 md:space-y-6">
          {steps.map((s, i) => (
            <div key={i} className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10 flex gap-4 md:gap-8 items-start">
              <div className="shrink-0">
                <span className="text-2xl md:text-3xl font-black text-white/35 block mb-2 md:mb-3">{s.num}</span>
                <span className={`inline-block px-2.5 md:px-3 py-1 md:py-1.5 rounded-full text-[10px] md:text-xs font-bold ${s.color}`}>{s.badge}</span>
              </div>
              <div>
                <div className="flex items-center gap-2 md:gap-3 mb-1 md:mb-2">
                  <h3 className="text-lg md:text-xl font-bold">{s.title}</h3>
                  <span className="text-xs md:text-sm text-white/30">{s.week}</span>
                </div>
                <p className="text-white/55 leading-relaxed text-sm md:text-base">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Live Demo ───────────────────────────────────────── */
function LiveDemo() {
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const callApi = async () => {
    setLoading(true);
    try {
      const res = await fetch("https://airbridge-entry-api-prototype.onrender.com/v1/entry/predict", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ app_id: "ablog", airbridge_uuid: "363c178f-ad44-4e18-ad81-ed098e28919f" }),
      });
      setResponse(JSON.stringify(await res.json(), null, 2));
    } catch { setResponse("// Server waking up. Try again in 30s."); }
    setLoading(false);
  };
  return (
    <section id="demo" className="py-12 md:py-20 px-6 relative">
      <div className="section-divider max-w-5xl mx-auto mb-8 md:mb-16" />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10 md:mb-16">
          <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">Live Demo</p>
          <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight">See it <span className="gradient-text">for yourself.</span></h2>
          <p className="text-white/55 text-base md:text-lg mt-4">Real production API. Not a mockup.</p>
        </div>
        <div className="card-glass rounded-2xl md:rounded-3xl p-5 md:p-10">
          <div className="flex items-center justify-between mb-4 md:mb-6">
            <div className="flex items-center gap-1.5 md:gap-2">
              <span className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-[#ff5f57]" />
              <span className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-[#febc2e]" />
              <span className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-[#28c840]" />
              <span className="text-[10px] md:text-xs text-white/30 ml-2 md:ml-4 font-mono">terminal</span>
            </div>
            <button onClick={() => {
              const cmd = `curl -X POST https://airbridge-entry-api-prototype.onrender.com/v1/entry/predict \\
  -H "Content-Type: application/json" \\
  -d '{"app_id":"ablog","airbridge_uuid":"363c178f-ad44-4e18-ad81-ed098e28919f"}'`;
              navigator.clipboard.writeText(cmd.replace(/\\\\/g, '\\'));
              setCopied(true); setTimeout(() => setCopied(false), 2000);
            }}
              className="btn-primary text-white px-4 md:px-6 py-2 md:py-2.5 rounded-full text-xs md:text-sm font-semibold">
              {copied ? "Copied!" : "Copy to Clipboard"}
            </button>
          </div>
          <pre className="code-block p-4 md:p-6 mb-4 overflow-x-auto text-white/55 text-xs md:text-sm select-all cursor-pointer" title="Click to select, then Cmd+C to copy">{`curl -X POST https://airbridge-entry-api-prototype.onrender.com/v1/entry/predict \\
  -H "Content-Type: application/json" \\
  -d '{"app_id":"ablog","airbridge_uuid":"363c178f-ad44-4e18-ad81-ed098e28919f"}'`}</pre>
          <p className="text-[10px] text-white/30 mb-6">Click the command to select, then copy and paste into your terminal.</p>
          
          <p className="text-[10px] md:text-xs text-white/30 mb-2 uppercase tracking-widest font-semibold">
            {response ? "Live Response" : "Example Response"}
          </p>
          <pre className="code-block p-4 md:p-6 overflow-x-auto text-[#3d8bff] text-xs md:text-sm">{response || `{
  "user_id": "363c178f-ad44-4e18-ad81-ed098e28919f",
  "best_trigger": "social_proof",
  "trigger_scores": {
    "price_appeal": 0.18,
    "social_proof": 0.28,
    "scarcity": 0.20,
    "novelty": 0.19
  },
  "is_random": false,
  "d3_purchase_prob": 0.22,
  "d3_churn_prob": 0.34,
  "pltv": {
    "tier": "medium",
    "percentile": 59,
    "tier_avg_ltv": 9338
  }
}`}</pre>
          <p className="text-[10px] text-white/35 mt-3">
            {response ? "" : "⚠️ Demo server may take ~30s to wake up on first request (free tier). Production API responds in <200ms."}
          </p>
        </div>
      </div>
    </section>
  );
}

/* ── Integration CTA ─────────────────────────────────── */
function Integration() {
  const steps = [
    { num: "01", title: "Tag SDK events", desc: "Core app events (views, signups, purchases). Most already tagged if you use Airbridge." },
    { num: "02", title: "Design 4 modals", desc: "Price Appeal, Social Proof, Scarcity, Novelty. Same format, different hook." },
    { num: "03", title: "Call one endpoint", desc: "POST with app_id + uuid. 5 min after app open. We handle the rest." },
  ];
  return (
    <section id="start" className="py-16 md:py-24 px-6 relative">
      <div className="aurora" />
      <div className="relative z-10 max-w-5xl mx-auto text-center">
        <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">Integration</p>
        <h2 className="text-xl md:text-[2.5rem] font-bold tracking-tight mb-4 md:mb-6">
          You do <span className="gradient-text">3 things</span>.<br />We do everything else.
        </h2>
        <p className="text-white/55 text-base md:text-lg mb-12 md:mb-20 max-w-2xl mx-auto">
          Data pipeline, model training, experiment design, weekly retraining, real-time serving.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-12 md:mb-20">
          {steps.map((s) => (
            <div key={s.num} className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10 text-left">
              <span className="text-4xl md:text-5xl font-black text-white/20 block mb-4 md:mb-6">{s.num}</span>
              <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3">{s.title}</h3>
              <p className="text-xs md:text-sm text-white/55 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
        <a href="#contact" className="btn-primary inline-block text-white px-10 md:px-14 py-4 md:py-5 rounded-full font-bold text-base md:text-xl">
          Get Started &rarr;
        </a>
        <p className="mt-4 md:mt-6 text-xs md:text-sm text-white/30">Live in 1 week. No commitment required.</p>
      </div>
    </section>
  );
}

/* ── Contact Form ─────────────────────────────────── */
function ContactForm() {
  const [form, setForm] = useState({ name: '', email: '', company: '', message: '' });
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    try {
      // Google Apps Script Web App URL — replace with your deployed script URL
      const SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxFEHPaStlCt84u-zgRr24gCVvsgHzeWoVVTq9Fe8wsF0ZV60NSsA29-CW6j91UWUE/exec';
      await fetch(SCRIPT_URL, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, timestamp: new Date().toISOString() }),
      });
      setSent(true);
    } catch {
      setSent(true); // no-cors always succeeds
    }
    setSending(false);
  };

  return (
    <section id="contact" className="py-16 md:py-24 px-6 relative">
      <div className="aurora" />
      <div className="relative z-10 max-w-2xl mx-auto">
        <div className="text-center mb-8 md:mb-12">
          <p className="text-sm font-semibold text-[#0062FA] tracking-widest uppercase mb-4">Get Started</p>
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight">
            Ready to <span className="gradient-text">personalize</span> from day one?
          </h2>
          <p className="text-white/55 text-base md:text-lg mt-4">
            Leave your info. We&apos;ll set up a pilot within a week.
          </p>
        </div>

        {sent ? (
          <div className="card-glass rounded-2xl md:rounded-3xl p-10 text-center">
            <p className="text-3xl mb-4">\u2705</p>
            <h3 className="text-2xl font-bold mb-2">Thank you!</h3>
            <p className="text-white/40">We&apos;ll reach out within 24 hours.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="card-glass rounded-2xl md:rounded-3xl p-6 md:p-10 space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-white/30 mb-1.5 uppercase tracking-wider">Name *</label>
                <input required type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                  className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder-white/20 focus:border-[#0062FA]/50 focus:outline-none transition"
                  placeholder="John Kim" />
              </div>
              <div>
                <label className="block text-xs text-white/30 mb-1.5 uppercase tracking-wider">Work Email *</label>
                <input required type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})}
                  className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder-white/20 focus:border-[#0062FA]/50 focus:outline-none transition"
                  placeholder="john@company.com" />
              </div>
            </div>
            <div>
              <label className="block text-xs text-white/30 mb-1.5 uppercase tracking-wider">Company / App Name *</label>
              <input required type="text" value={form.company} onChange={e => setForm({...form, company: e.target.value})}
                className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder-white/20 focus:border-[#0062FA]/50 focus:outline-none transition"
                placeholder="Your App" />
            </div>
            <div>
              <label className="block text-xs text-white/30 mb-1.5 uppercase tracking-wider">Anything else?</label>
              <textarea value={form.message} onChange={e => setForm({...form, message: e.target.value})}
                className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder-white/20 focus:border-[#0062FA]/50 focus:outline-none transition h-24 resize-none"
                placeholder="Monthly new users, current SDK setup, questions..." />
            </div>
            <button type="submit" disabled={sending}
              className="btn-primary w-full text-white py-4 rounded-full font-bold text-lg disabled:opacity-50">
              {sending ? "Sending..." : "Get Started \u2192"}
            </button>
            <p className="text-center text-xs text-white/30">No commitment. We respond within 24 hours.</p>
          </form>
        )}
      </div>
    </section>
  );
}

/* ── Footer ──────────────────────────────────────────── */
function Footer() {
  return (
    <footer className="border-t border-white/[0.08] py-10 md:py-16 px-6">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-8">
        <div className="flex items-center gap-3 md:gap-4">
          <Image src="/airbridge-logo.png" alt="Airbridge" width={100} height={22} style={{width:'auto',height:'auto'}} />
          <span className="text-white/30">|</span>
          <span className="text-white/55 text-sm font-medium">Entry API</span>
        </div>
        <p className="text-xs md:text-sm text-white/30 italic">Personalization from the very first moment.</p>
        <p className="text-xs text-white/30">&copy; {new Date().getFullYear()} AB180, Inc.</p>
      </div>
    </footer>
  );
}

export default function Home() {
  return (<><Nav /><Hero /><Problem /><HowPossible /><WhyAirbridge /><Features /><Proof /><HowItWorks /><LiveDemo /><Integration /><ContactForm /><Footer /></>);
}
