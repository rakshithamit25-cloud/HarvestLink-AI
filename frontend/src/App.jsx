import React, { useState, useEffect, useRef } from 'react';
import { translations } from './i18n';
import { api } from './api';
import { 
  Mic, MicOff, Volume2, ShieldCheck, CheckCircle2, Clock, AlertTriangle, 
  RefreshCw, Play, ArrowRight, DollarSign, Package, ShoppingCart, UserCheck, 
  MapPin, Sparkles, Building2, Store, Factory, HelpCircle, Layers
} from 'lucide-react';

// 6 Picture-based crop cards
const CROPS = [
  { name: "Tomato", ta: "தக்காளி", icon: "🍅", defaultExpected: 1.00, defaultMin: 0.90 },
  { name: "Onion", ta: "வெங்காயம்", icon: "🧅", defaultExpected: 0.80, defaultMin: 0.70 },
  { name: "Brinjal", ta: "கத்தரிக்காய்", icon: "🍆", defaultExpected: 0.60, defaultMin: 0.50 },
  { name: "Potato", ta: "உருளைக்கிழங்கு", icon: "🥔", defaultExpected: 0.70, defaultMin: 0.60 },
  { name: "Carrot", ta: "கேரட்", icon: "🥕", defaultExpected: 1.20, defaultMin: 1.00 },
  { name: "Okra", ta: "வெண்டைக்காய்", icon: "🌿", defaultExpected: 0.90, defaultMin: 0.75 }
];

export default function App() {
  const [lang, setLang] = useState('ta');
  const t = translations[lang] || translations.en;
  
  const [role, setRole] = useState('farmer'); // 'farmer', 'buyer', 'operator'
  const [loading, setLoading] = useState(false);
  const [demoBanner, setDemoBanner] = useState(null);

  // Listing Form State
  const [selectedCrop, setSelectedCrop] = useState(CROPS[0]);
  const [quantity, setQuantity] = useState("500");
  const [expectedPrice, setExpectedPrice] = useState("1.00");
  const [minimumPrice, setMinimumPrice] = useState("0.90");
  const [location, setLocation] = useState("Salem");
  const [harvestDate, setHarvestDate] = useState("2026-11-08");
  const [freshness, setFreshness] = useState("fresh");
  
  // Voice Input State
  const [isListening, setIsListening] = useState(false);
  const [speechTranscript, setSpeechTranscript] = useState("");
  const [speechSupported, setSpeechSupported] = useState(true);
  const [audioFeedback, setAudioFeedback] = useState("");

  // Operator Consent State
  const [operatorFarmerName, setOperatorFarmerName] = useState("Kumar");
  const [consentMethod, setConsentMethod] = useState("verbal");
  const [consentChecked, setConsentChecked] = useState(false);

  // App Data
  const [listings, setListings] = useState([]);
  const [activeListing, setActiveListing] = useState(null);
  const [matches, setMatches] = useState([]);
  const [orders, setOrders] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [impactMetrics, setImpactMetrics] = useState(null);
  const [showLogsPanel, setShowLogsPanel] = useState(true);

  // Speech Recognition Setup
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = lang === 'ta' ? 'ta-IN' : 'en-US';
      
      recognition.onresult = async (event) => {
        const text = event.results[0][0].transcript;
        setSpeechTranscript(text);
        setIsListening(false);
        // Call backend parse endpoint
        try {
          const parsed = await api.parseVoiceText(text);
          if (parsed.crop_name) {
            const matchedCrop = CROPS.find(c => c.name.toLowerCase() === parsed.crop_name.toLowerCase());
            if (matchedCrop) setSelectedCrop(matchedCrop);
          }
          if (parsed.quantity) setQuantity(parsed.quantity.toString());
          if (parsed.expected_price) setExpectedPrice(parsed.expected_price.toString());
          if (parsed.location) setLocation(parsed.location);
        } catch (e) {
          console.error("Failed to parse speech text", e);
        }
      };

      recognition.onerror = () => {
        setIsListening(false);
      };
      recognition.onend = () => {
        setIsListening(false);
      };
      recognitionRef.current = recognition;
    } else {
      setSpeechSupported(false);
    }
    
    refreshData();
  }, [lang]);

  const refreshData = async () => {
    try {
      const [allListings, allOrders, logs, metrics] = await Promise.all([
        api.fetchListings(),
        api.fetchOrders(),
        api.fetchAgentLogs(),
        api.fetchImpactMetrics()
      ]);
      setListings(allListings);
      setOrders(allOrders);
      setAgentLogs(logs);
      setImpactMetrics(metrics);

      if (allListings.length > 0) {
        const first = allListings[0];
        setActiveListing(first);
        const matchData = await api.fetchMatches(first.id);
        setMatches(matchData);
      }
    } catch (e) {
      console.error("Data refresh error", e);
    }
  };

  const toggleListening = () => {
    if (!speechSupported || !recognitionRef.current) {
      alert(t.tamil_voice_not_supported);
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.lang = lang === 'ta' ? 'ta-IN' : 'en-US';
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  // Offer Audio Playback
  const playOfferAudio = (text) => {
    if (!('speechSynthesis' in window)) {
      setAudioFeedback(t.tamil_audio_not_available);
      return;
    }
    const voices = window.speechSynthesis.getVoices();
    const tamilVoice = voices.find(v => v.lang.includes('ta') || v.name.toLowerCase().includes('tamil'));
    
    const utterance = new SpeechSynthesisUtterance(text);
    if (tamilVoice) {
      utterance.voice = tamilVoice;
      utterance.lang = 'ta-IN';
      setAudioFeedback("Playing Tamil voice audio...");
    } else {
      setAudioFeedback(t.tamil_audio_not_available);
      utterance.lang = 'en-US';
    }
    window.speechSynthesis.speak(utterance);
  };

  // Run One-Click Kumar Demo Scenario
  const handleRunDemo = async () => {
    setLoading(true);
    setDemoBanner("Running Multi-Agent Negotiation & PayPal Sandbox Settlement...");
    try {
      const res = await api.runDemoScenario();
      setDemoBanner(`Scenario completed: 450 kg allocated across 3 buyers. Remaining: ${res.remaining_inventory_kg} kg. All orders settled in Sandbox USD.`);
      await refreshData();
    } catch (e) {
      setDemoBanner("Failed to run demo scenario.");
    } finally {
      setLoading(false);
    }
  };

  // Reset Demo
  const handleResetData = async () => {
    setLoading(true);
    try {
      await api.resetDemoData();
      setDemoBanner("Database reset to pristine seed data.");
      await refreshData();
    } catch (e) {
      alert("Error resetting data");
    } finally {
      setLoading(false);
    }
  };

  // Create Listing
  const handlePublishListing = async () => {
    setLoading(true);
    try {
      if (role === 'operator') {
        if (!consentChecked) {
          alert("Operator action requires explicit farmer consent verification.");
          setLoading(false);
          return;
        }
        await api.createOperatorListing({
          farmer_name: operatorFarmerName,
          consent_method: consentMethod,
          crop_name: selectedCrop.name,
          quantity: parseFloat(quantity),
          expected_price: parseFloat(expectedPrice),
          minimum_price: parseFloat(minimumPrice),
          location: location,
          harvest_date: harvestDate,
          freshness_status: freshness
        });
      } else {
        await api.createListing({
          crop_name: selectedCrop.name,
          quantity: parseFloat(quantity),
          expected_price: parseFloat(expectedPrice),
          minimum_price: parseFloat(minimumPrice),
          location: location,
          harvest_date: harvestDate,
          freshness_status: freshness
        });
      }
      await refreshData();
      alert("Produce listing successfully published!");
    } catch (e) {
      alert("Error creating listing");
    } finally {
      setLoading(false);
    }
  };

  // Run AI Agents on current listing
  const handleRunAgents = async () => {
    if (!activeListing) return;
    setLoading(true);
    try {
      await api.runMatching(activeListing.id, "rule-based");
      await refreshData();
    } catch (e) {
      alert("Error executing AI agents");
    } finally {
      setLoading(false);
    }
  };

  // Approve Match
  const handleApproveMatch = async (matchId, party) => {
    try {
      if (party === 'farmer') {
        await api.approveFarmerMatch(matchId, {
          consent_method: role === 'operator' ? consentMethod : 'verbal',
          farmer_name: role === 'operator' ? operatorFarmerName : 'Kumar'
        });
      } else {
        await api.approveBuyerMatch(matchId);
      }
      await refreshData();
    } catch (e) {
      alert("Approval rejected: check consent or authorization");
    }
  };

  // PayPal Sandbox Checkout
  const handlePayPalPay = async (orderId) => {
    setLoading(true);
    try {
      const payOrder = await api.createPayPalOrder(orderId);
      // Capture order
      await api.capturePayPalOrder(orderId, payOrder.paypal_order_id);
      await refreshData();
      alert("Payment captured and verified by backend server!");
    } catch (e) {
      alert("Payment processing failed");
    } finally {
      setLoading(false);
    }
  };

  // Confirm Delivery
  const handleConfirmDelivery = async (orderId) => {
    try {
      await api.confirmDelivery(orderId, {
        notes: "Produce delivered and inspected",
        consent_method: consentMethod,
        farmer_name: operatorFarmerName
      });
      await refreshData();
      alert("Delivery verified! Impact metrics updated.");
    } catch (e) {
      alert("Delivery confirmation error");
    }
  };

  return (
    <div className={`min-h-screen bg-slate-50 text-slate-900 pb-16 ${lang === 'ta' ? 'tamil-font' : ''}`}>
      {/* Top Notice: Mock Mode / Sandbox Banner */}
      <div className="bg-amber-500 text-slate-950 font-medium px-4 py-2 text-center text-xs md:text-sm flex items-center justify-center gap-2">
        <AlertTriangle className="w-4 h-4" />
        <span>{t.mock_mode_notice}</span>
      </div>

      {/* Main Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🌱</span>
            <div>
              <h1 className="text-xl font-bold text-agrigreen-800 tracking-tight">{t.app_title}</h1>
              <p className="text-xs text-slate-500 hidden sm:block">{t.tagline}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Language Selector */}
            <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button 
                onClick={() => setLang('ta')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition ${lang === 'ta' ? 'bg-agrigreen-700 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
              >
                தமிழ்
              </button>
              <button 
                onClick={() => setLang('en')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition ${lang === 'en' ? 'bg-agrigreen-700 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
              >
                English
              </button>
            </div>

            {/* Quick Demo Actions */}
            <button
              onClick={handleRunDemo}
              disabled={loading}
              className="bg-agrigreen-600 hover:bg-agrigreen-700 text-white text-xs md:text-sm font-semibold px-3 py-2 rounded-lg shadow-sm flex items-center gap-1.5 transition active:scale-95"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{t.run_demo}</span>
            </button>
            <button
              onClick={handleResetData}
              disabled={loading}
              title={t.reset_data}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 p-2 rounded-lg border border-slate-200 transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Role Navigation Bar */}
      <div className="bg-slate-100 border-b border-slate-200 py-2">
        <div className="max-w-7xl mx-auto px-4 flex gap-2">
          <button
            onClick={() => setRole('farmer')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition ${role === 'farmer' ? 'bg-white shadow text-agrigreen-800 border border-slate-200' : 'text-slate-600 hover:bg-slate-200'}`}
          >
            <span>👨‍🌾</span> {t.farmer}
          </button>
          <button
            onClick={() => setRole('buyer')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition ${role === 'buyer' ? 'bg-white shadow text-agrigreen-800 border border-slate-200' : 'text-slate-600 hover:bg-slate-200'}`}
          >
            <span>🏢</span> {t.buyer}
          </button>
          <button
            onClick={() => setRole('operator')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition ${role === 'operator' ? 'bg-white shadow text-agrigreen-800 border border-slate-200' : 'text-slate-600 hover:bg-slate-200'}`}
          >
            <span>🤝</span> {t.operator}
          </button>
        </div>
      </div>

      {/* Demo Status Banner */}
      {demoBanner && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-4 py-3 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>{demoBanner}</span>
            </div>
            <button onClick={() => setDemoBanner(null)} className="text-xs text-emerald-700 underline">Dismiss</button>
          </div>
        </div>
      )}

      {/* Impact Metric Header Ribbon */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
            <p className="text-xs text-slate-500 font-medium">Listed Produce</p>
            <p className="text-xl font-bold text-slate-800">{impactMetrics ? impactMetrics.listed_quantity : 500} <span className="text-xs font-normal text-slate-500">kg</span></p>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
            <p className="text-xs text-slate-500 font-medium">AI Matched</p>
            <p className="text-xl font-bold text-amber-600">{impactMetrics ? impactMetrics.matched_quantity : 450} <span className="text-xs font-normal text-slate-500">kg</span></p>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
            <p className="text-xs text-slate-500 font-medium">Orders Confirmed</p>
            <p className="text-xl font-bold text-blue-600">{impactMetrics ? impactMetrics.confirmed_quantity : 0} <span className="text-xs font-normal text-slate-500">kg</span></p>
          </div>
          <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-200 shadow-sm">
            <p className="text-xs text-emerald-800 font-semibold">{t.waste_prevented_stat}</p>
            <p className="text-xl font-bold text-emerald-700">{impactMetrics ? impactMetrics.delivered_quantity : 0} <span className="text-xs font-normal text-slate-500">kg</span></p>
          </div>
          <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm col-span-2 sm:col-span-1">
            <p className="text-xs text-slate-500 font-medium">Remaining Stock</p>
            <p className="text-xl font-bold text-slate-700">{impactMetrics ? impactMetrics.remaining_unsold_quantity : 50} <span className="text-xs font-normal text-slate-500">kg</span></p>
          </div>
        </div>
      </div>

      {/* Main Content Workspace */}
      <main className="max-w-7xl mx-auto px-4 mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Input Form (Farmer / Operator) */}
        <section className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <span>{role === 'operator' ? '🤝' : '🎙️'}</span>
                <span>{role === 'operator' ? t.operator_consent_title : t.voice_input_title}</span>
              </h2>
              <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-medium">
                {role === 'operator' ? 'Operator Mode' : 'Farmer Voice'}
              </span>
            </div>

            {/* Operator Consent Form Box */}
            {role === 'operator' && (
              <div className="mb-5 bg-amber-50 p-4 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-3">
                <p className="font-semibold text-amber-950">{t.operator_consent_desc}</p>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">{t.farmer_name_label}</label>
                  <input
                    type="text"
                    value={operatorFarmerName}
                    onChange={(e) => setOperatorFarmerName(e.target.value)}
                    className="w-full bg-white border border-amber-300 rounded-lg p-2 text-sm"
                    placeholder="Enter offline farmer's full name"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">{t.consent_method_label}</label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input 
                        type="radio" 
                        name="consent" 
                        value="verbal" 
                        checked={consentMethod === 'verbal'} 
                        onChange={() => setConsentMethod('verbal')} 
                      />
                      <span>{t.consent_verbal}</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input 
                        type="radio" 
                        name="consent" 
                        value="written" 
                        checked={consentMethod === 'written'} 
                        onChange={() => setConsentMethod('written')} 
                      />
                      <span>{t.consent_written}</span>
                    </label>
                  </div>
                </div>
                <div className="pt-2 border-t border-amber-200">
                  <label className="flex items-start gap-2 cursor-pointer font-medium text-slate-800">
                    <input 
                      type="checkbox" 
                      checked={consentChecked} 
                      onChange={(e) => setConsentChecked(e.target.checked)} 
                      className="mt-0.5 rounded text-agrigreen-600"
                    />
                    <span>I verify that farmer {operatorFarmerName || '[Farmer Name]'} gave explicit {consentMethod} consent to list this produce.</span>
                  </label>
                </div>
              </div>
            )}

            {/* Voice Input Microphone Widget */}
            <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200 text-center">
              <p className="text-xs text-slate-600 mb-3 font-medium">
                {lang === 'ta' ? t.voice_hint_tamil : t.voice_hint}
              </p>
              
              <button
                onClick={toggleListening}
                className={`w-20 h-20 rounded-full mx-auto flex items-center justify-center transition shadow-md active:scale-95 ${
                  isListening ? 'bg-red-500 animate-pulse text-white' : 'bg-agrigreen-600 hover:bg-agrigreen-700 text-white'
                }`}
              >
                {isListening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
              </button>

              <p className="text-xs text-slate-500 mt-2 font-medium">
                {isListening ? t.listening : t.start_speaking}
              </p>

              {speechTranscript && (
                <div className="mt-3 p-2.5 bg-white border border-slate-200 rounded-lg text-left text-xs text-slate-700">
                  <span className="font-semibold text-slate-500 block mb-0.5">Voice Heard:</span>
                  "{speechTranscript}"
                </div>
              )}
            </div>

            {/* Picture-based Crop Selection (6 Crops) */}
            <div className="mb-5">
              <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wider">{t.crop}</label>
              <div className="grid grid-cols-3 gap-2">
                {CROPS.map((crop) => (
                  <button
                    key={crop.name}
                    type="button"
                    onClick={() => {
                      setSelectedCrop(crop);
                      setExpectedPrice(crop.defaultExpected.toFixed(2));
                      setMinimumPrice(crop.defaultMin.toFixed(2));
                    }}
                    className={`p-2.5 rounded-xl border text-center transition flex flex-col items-center gap-1 ${
                      selectedCrop.name === crop.name 
                        ? 'border-agrigreen-600 bg-agrigreen-50 text-agrigreen-900 font-bold ring-2 ring-agrigreen-500/20' 
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                    }`}
                  >
                    <span className="text-2xl">{crop.icon}</span>
                    <span className="text-xs">{lang === 'ta' ? crop.ta : crop.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">{t.quantity_kg}</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">{t.location}</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-5">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">{t.asking_price}</label>
                <input
                  type="number"
                  step="0.05"
                  value={expectedPrice}
                  onChange={(e) => setExpectedPrice(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">{t.minimum_price}</label>
                <input
                  type="number"
                  step="0.05"
                  value={minimumPrice}
                  onChange={(e) => setMinimumPrice(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                />
              </div>
            </div>

            {/* Publish Button */}
            <button
              onClick={handlePublishListing}
              disabled={loading}
              className="w-full py-3 bg-agrigreen-700 hover:bg-agrigreen-800 text-white font-bold rounded-xl shadow-md transition active:scale-95 flex items-center justify-center gap-2"
            >
              <span>✅</span>
              <span>{role === 'operator' ? t.record_and_publish : t.publish_listing}</span>
            </button>
          </div>
        </section>

        {/* Right Column: Matching, Negotiations & PayPal Flow */}
        <section className="lg:col-span-7 space-y-6">
          
          {/* Active Listing & Match Header */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
              <div>
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" />
                  <span>{t.matching_title}</span>
                </h2>
                <p className="text-xs text-slate-500">
                  {activeListing ? `Active Listing: ${activeListing.crop_name} (${activeListing.available_quantity} kg available / ${activeListing.quantity} kg total)` : 'No active listing'}
                </p>
              </div>

              <button
                onClick={handleRunAgents}
                disabled={loading || !activeListing}
                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition active:scale-95 shadow-sm"
              >
                <Sparkles className="w-4 h-4" />
                <span>Run Agent Negotiation</span>
              </button>
            </div>

            {/* Matches List */}
            <div className="mt-4 space-y-3">
              {matches.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-sm">
                  Click "Run Agent Negotiation" or run the demo to view multi-buyer allocations.
                </div>
              ) : (
                matches.map((m) => (
                  <div key={m.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 hover:border-slate-300 transition">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="p-2 bg-white rounded-lg border border-slate-200 text-lg">
                          {m.buyer_name?.includes('Restaurant') ? '🍽️' : m.buyer_name?.includes('Supermarket') ? '🛒' : '🏭'}
                        </span>
                        <div>
                          <p className="text-sm font-bold text-slate-800">{m.buyer_name || 'Buyer'}</p>
                          <p className="text-xs text-slate-500">{m.crop_name} • {m.allocated_quantity} kg allocated</p>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <div>
                        {m.status === 'confirmed' ? (
                          <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full">
                            ✅ Confirmed Deal
                          </span>
                        ) : m.status === 'farmer_approved' ? (
                          <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2.5 py-1 rounded-full">
                            Farmer Approved
                          </span>
                        ) : m.status === 'buyer_approved' ? (
                          <span className="text-xs font-semibold text-indigo-700 bg-indigo-100 px-2.5 py-1 rounded-full">
                            Buyer Approved
                          </span>
                        ) : m.status === 'no_overlap' ? (
                          <span className="text-xs font-semibold text-rose-700 bg-rose-100 px-2.5 py-1 rounded-full">
                            No Price Overlap
                          </span>
                        ) : (
                          <span className="text-xs font-semibold text-amber-700 bg-amber-100 px-2.5 py-1 rounded-full">
                            Proposed Match
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Price details: separated and clearly labeled */}
                    <div className="grid grid-cols-3 gap-2 my-2.5 p-2 bg-white rounded-lg border border-slate-100 text-xs">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Farmer Ask</span>
                        <span className="font-semibold text-slate-700">${m.farmer_asking_price.toFixed(2)}/kg</span>
                      </div>
                      <div>
                        <span className="text-amber-600 block text-[10px] font-medium">{t.suggested_price_label}</span>
                        <span className="font-bold text-amber-700">${m.ai_suggested_price.toFixed(2)}/kg</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Agreed Price</span>
                        <span className="font-bold text-emerald-700">
                          {m.agreed_price ? `$${m.agreed_price.toFixed(2)}/kg` : 'Pending'}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 mb-3 bg-white/60 p-2 rounded border border-slate-100">
                      ℹ️ {m.match_reason}
                    </p>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-200/60">
                      {/* Audio Playback button */}
                      <button
                        onClick={() => playOfferAudio(`${m.buyer_name} ${m.allocated_quantity} கிலோ தக்காளியை ஒரு கிலோவுக்கு ${m.ai_suggested_price} டாலருக்கு வாங்க சம்மதிக்கிறது.`)}
                        className="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>{t.audio_offer_playback}</span>
                      </button>

                      {/* Farmer Consent / Approve Button */}
                      {m.status !== 'confirmed' && m.status !== 'farmer_approved' && (
                        <button
                          onClick={() => handleApproveMatch(m.id, 'farmer')}
                          className="text-xs bg-agrigreen-600 hover:bg-agrigreen-700 text-white font-semibold px-3 py-1.5 rounded-lg transition"
                        >
                          {role === 'operator' ? 'Approve with Consent' : 'Farmer Accept'}
                        </button>
                      )}

                      {/* Buyer Approve Button */}
                      {m.status !== 'confirmed' && m.status !== 'buyer_approved' && (
                        <button
                          onClick={() => handleApproveMatch(m.id, 'buyer')}
                          className="text-xs bg-blue-600 hover:bg-blue-700 text-white font-semibold px-3 py-1.5 rounded-lg transition"
                        >
                          Buyer Approve
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {audioFeedback && (
              <p className="text-xs text-amber-800 mt-2 font-medium">{audioFeedback}</p>
            )}
          </div>

          {/* Orders & PayPal Sandbox Checkout Table */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-agrigreen-700" />
              <span>Orders & PayPal Sandbox Settlement</span>
            </h2>

            {orders.length === 0 ? (
              <p className="text-xs text-slate-400">No confirmed orders yet. Once both parties approve a deal, orders appear here for payment.</p>
            ) : (
              <div className="space-y-3">
                {orders.map((o) => (
                  <div key={o.id} className="p-3.5 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50">
                    <div>
                      <p className="text-xs font-bold text-slate-800">
                        Order #{o.id} • {o.crop_name} ({o.quantity} kg)
                      </p>
                      <p className="text-xs text-slate-500">
                        Buyer: {o.buyer_name} • Agreed: ${o.agreed_price.toFixed(2)}/kg • Total: <span className="font-bold text-slate-800">${o.total_amount.toFixed(2)} USD</span>
                      </p>
                      <span className={`inline-block mt-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                        o.payment_status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        Payment: {o.payment_status.toUpperCase()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {o.payment_status !== 'completed' ? (
                        <button
                          onClick={() => handlePayPalPay(o.id)}
                          className="bg-[#0070ba] hover:bg-[#003087] text-white text-xs font-bold px-3 py-2 rounded-lg flex items-center gap-1.5 shadow-sm transition"
                        >
                          <span>PayPal Sandbox</span>
                        </button>
                      ) : o.order_status !== 'delivered' ? (
                        <button
                          onClick={() => handleConfirmDelivery(o.id)}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-2 rounded-lg flex items-center gap-1 shadow-sm transition"
                        >
                          <span>Verify Delivery</span>
                        </button>
                      ) : (
                        <span className="text-xs text-emerald-700 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" /> Delivered & Verified
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Agent Activity Panel */}
          <div className="bg-slate-900 text-slate-100 p-5 rounded-2xl shadow-lg border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-agrigreen-500" />
                <h3 className="text-sm font-bold tracking-wide uppercase text-slate-200">{t.agent_activity_title}</h3>
              </div>
              <button 
                onClick={() => setShowLogsPanel(!showLogsPanel)}
                className="text-xs text-slate-400 hover:text-white underline"
              >
                {showLogsPanel ? 'Hide Logs' : 'Show Logs'}
              </button>
            </div>

            {showLogsPanel && (
              <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1 text-xs">
                {agentLogs.length === 0 ? (
                  <p className="text-slate-500 text-center py-4">No agent logs recorded yet. Run matching or demo scenario to view live logs.</p>
                ) : (
                  agentLogs.map((log) => (
                    <div key={log.id} className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                          <span>🤖</span> {log.agent_name}
                        </span>
                        <div className="flex items-center gap-2 text-[10px]">
                          <span className="bg-slate-700 text-amber-300 px-2 py-0.5 rounded font-mono">
                            Mode: {log.mode}
                          </span>
                          <span className="text-slate-400 font-mono">
                            {log.execution_time_ms} ms
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-300 font-medium mb-1">Task: {log.task}</p>
                      <p className="text-slate-400 text-[11px]">Input: {log.input_summary}</p>
                      <p className="text-slate-300 text-[11px] font-semibold mt-1">Output: {log.output_summary}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

        </section>
      </main>
    </div>
  );
}
