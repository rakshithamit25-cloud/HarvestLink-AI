import React, { useState, useEffect, useRef } from 'react';
import { translations } from './i18n';
import { api } from './api';
import {
  Mic, MicOff, Volume2, ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  RefreshCw, Play, ArrowRight, DollarSign, Package, ShoppingCart, UserCheck,
  MapPin, Sparkles, Building2, Store, Factory, HelpCircle, Layers, Search, X
} from 'lucide-react';

// Categories: vegetables, fruits, pulses and grains, spices, others (30+ common Tamil Nadu crops)
const ALL_CROP_CATEGORIES = [
  {
    key: "vegetables",
    labelKey: "crop_category_vegetables",
    crops: [
      { name: "Tomato", ta: "தக்காளி", icon: "🍅", defaultExpected: 1.00, defaultMin: 0.90 },
      { name: "Onion", ta: "வெங்காயம்", icon: "🧅", defaultExpected: 0.80, defaultMin: 0.70 },
      { name: "Brinjal", ta: "கத்தரிக்காய்", icon: "🍆", defaultExpected: 0.60, defaultMin: 0.50 },
      { name: "Potato", ta: "உருளைக்கிழங்கு", icon: "🥔", defaultExpected: 0.70, defaultMin: 0.60 },
      { name: "Chilli", ta: "மிளகாய்", icon: "🌶️", defaultExpected: 1.50, defaultMin: 1.20 },
      { name: "Okra", ta: "வெண்டைக்காய்", icon: "🌿", defaultExpected: 0.90, defaultMin: 0.75 },
      { name: "Carrot", ta: "கேரட்", icon: "🥕", defaultExpected: 1.20, defaultMin: 1.00 },
      { name: "Cabbage", ta: "முட்டைக்கோஸ்", icon: "🥬", defaultExpected: 0.50, defaultMin: 0.40 },
      { name: "Cauliflower", ta: "காலிஃபிளவர்", icon: "🥦", defaultExpected: 0.70, defaultMin: 0.60 },
      { name: "Beans", ta: "பீன்ஸ்", icon: "🫘", defaultExpected: 1.10, defaultMin: 0.90 },
      { name: "Drumstick", ta: "முருங்கைக்காய்", icon: "🌱", defaultExpected: 1.00, defaultMin: 0.80 },
      { name: "Bitter Gourd", ta: "பாகற்காய்", icon: "🥝", defaultExpected: 0.80, defaultMin: 0.65 },
      { name: "Pumpkin", ta: "பூசணிக்காய்", icon: "🎃", defaultExpected: 0.40, defaultMin: 0.30 },
      { name: "Cucumber", ta: "வெள்ளரிக்காய்", icon: "🥒", defaultExpected: 0.60, defaultMin: 0.50 },
      { name: "Radish", ta: "முள்ளங்கி", icon: "🫚", defaultExpected: 0.50, defaultMin: 0.40 },
      { name: "Beetroot", ta: "பீட்ரூட்", icon: "🫀", defaultExpected: 0.70, defaultMin: 0.55 },
    ]
  },
  {
    key: "fruits",
    labelKey: "crop_category_fruits",
    crops: [
      { name: "Coconut", ta: "தேங்காய்", icon: "🥥", defaultExpected: 0.20, defaultMin: 0.15 },
      { name: "Banana", ta: "வாழைப்பழம்", icon: "🍌", defaultExpected: 0.50, defaultMin: 0.40 },
      { name: "Mango", ta: "மாம்பழம்", icon: "🥭", defaultExpected: 1.50, defaultMin: 1.20 },
      { name: "Papaya", ta: "பப்பாளி", icon: "🍈", defaultExpected: 0.60, defaultMin: 0.50 },
      { name: "Guava", ta: "கொய்யா", icon: "🍏", defaultExpected: 0.80, defaultMin: 0.65 },
      { name: "Pomegranate", ta: "மாதுளை", icon: "🍎", defaultExpected: 1.80, defaultMin: 1.50 },
      { name: "Watermelon", ta: "தர்பூசணி", icon: "🍉", defaultExpected: 0.30, defaultMin: 0.25 },
      { name: "Pineapple", ta: "அன்னாசி", icon: "🍍", defaultExpected: 0.70, defaultMin: 0.55 },
      { name: "Grapes", ta: "திராட்சை", icon: "🍇", defaultExpected: 1.20, defaultMin: 1.00 },
      { name: "Lemon", ta: "எலுமிச்சை", icon: "🍋", defaultExpected: 1.20, defaultMin: 1.00 },
    ]
  },
  {
    key: "pulses_grains",
    labelKey: "crop_category_pulses_grains",
    crops: [
      { name: "Rice", ta: "அரிசி", icon: "🌾", defaultExpected: 0.40, defaultMin: 0.35 },
      { name: "Maize", ta: "மக்காச்சோளம்", icon: "🌽", defaultExpected: 0.25, defaultMin: 0.20 },
      { name: "Groundnut", ta: "கடலை (வேர்க்கடலை)", icon: "🥜", defaultExpected: 0.80, defaultMin: 0.65 },
      { name: "Black Gram", ta: "உளுந்து", icon: "⚫", defaultExpected: 0.90, defaultMin: 0.75 },
      { name: "Green Gram", ta: "பாசிப்பருப்பு", icon: "🟢", defaultExpected: 0.85, defaultMin: 0.70 },
      { name: "Wheat", ta: "கோதுமை", icon: "🌾", defaultExpected: 0.35, defaultMin: 0.30 },
      { name: "Finger Millet", ta: "ராகி", icon: "🌾", defaultExpected: 0.30, defaultMin: 0.25 },
    ]
  },
  {
    key: "spices",
    labelKey: "crop_category_spices",
    crops: [
      { name: "Turmeric", ta: "மஞ்சள்", icon: "🟡", defaultExpected: 1.50, defaultMin: 1.20 },
      { name: "Ginger", ta: "இஞ்சி", icon: "🫚", defaultExpected: 1.80, defaultMin: 1.50 },
      { name: "Garlic", ta: "பூண்டு", icon: "🧄", defaultExpected: 2.00, defaultMin: 1.60 },
      { name: "Coriander", ta: "கொத்தமல்லி", icon: "🌿", defaultExpected: 1.20, defaultMin: 0.95 },
      { name: "Black Pepper", ta: "மிளகு", icon: "⚫", defaultExpected: 4.00, defaultMin: 3.20 },
      { name: "Cardamom", ta: "ஏலக்காய்", icon: "🌿", defaultExpected: 8.00, defaultMin: 6.50 },
    ]
  },
  {
    key: "others",
    labelKey: "crop_category_others",
    crops: [
      { name: "Sugarcane", ta: "கரும்பு", icon: "🎋", defaultExpected: 0.08, defaultMin: 0.06 },
      { name: "Cotton", ta: "பருத்தி", icon: "☁️", defaultExpected: 0.70, defaultMin: 0.55 },
      { name: "Tea", ta: "தேயிலை", icon: "🍵", defaultExpected: 1.20, defaultMin: 0.95 },
      { name: "Coffee", ta: "காப்பி", icon: "☕", defaultExpected: 2.00, defaultMin: 1.60 },
    ]
  }
];

const ALL_CROPS = ALL_CROP_CATEGORIES.flatMap(category => category.crops);
const CROPS = ALL_CROPS;
const QUICK_BUYER_CROPS = ALL_CROPS.slice(0, 6);

// Validates that an approval URL points to the trusted PayPal Sandbox checkout domain
function isValidPayPalSandboxUrl(urlStr) {
  try {
    const parsed = new URL(urlStr);
    if (parsed.protocol !== 'https:') return false;
    const hostname = parsed.hostname.toLowerCase();
    return hostname === 'sandbox.paypal.com' || hostname === 'www.sandbox.paypal.com';
  } catch (e) {
    return false;
  }
}

export default function App() {
  const [lang, setLang] = useState('ta');
  const t = translations[lang] || translations.en;

  const [role, setRole] = useState('farmer'); // 'farmer', 'buyer', 'operator'
  const [loading, setLoading] = useState(false);
  const [demoBanner, setDemoBanner] = useState(null);
  const [paymentBanner, setPaymentBanner] = useState(null);
  const captureAttemptedRef = useRef(false);

  const [paypalMode, setPaypalMode] = useState('unknown');

  useEffect(() => {
    api.fetchPayPalConfig()
      .then((data) => setPaypalMode(data.paypal_mode || 'unknown'))
      .catch(() => setPaypalMode('unknown'));
  }, []);

  // Auth & Mobile OTP State
  const [currentUser, setCurrentUser] = useState(() => api.getStoredUser());
  const [isVerifyingSession, setIsVerifyingSession] = useState(true);
  const [loginPhone, setLoginPhone] = useState("+91-9876543210");
  const [loginOtp, setLoginOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [demoOtpDisplay, setDemoOtpDisplay] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [authSuccess, setAuthSuccess] = useState(null);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);

  // Validate session on mount / refresh
  useEffect(() => {
    let isMounted = true;
    const verifyAuth = async () => {
      try {
        const user = await api.validateSession();
        if (isMounted) {
          if (user) {
            setCurrentUser(user);
            if (user.role) {
              setRole(user.role);
            }
            refreshData();
          } else {
            setCurrentUser(null);
          }
        }
      } catch (err) {
        if (isMounted) setCurrentUser(null);
      } finally {
        if (isMounted) setIsVerifyingSession(false);
      }
    };
    verifyAuth();
    return () => { isMounted = false; };
  }, []);

  // Listing Form State
  const [selectedCrop, setSelectedCrop] = useState(CROPS[0]);
  const [cropCategory, setCropCategory] = useState('all');
  const [cropSearchQuery, setCropSearchQuery] = useState('');
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
  const [quantityCandidates, setQuantityCandidates] = useState(null); // null or array when needs_confirmation

  // Operator Consent State
  const [operatorFarmerName, setOperatorFarmerName] = useState("Kumar");
  const [consentMethod, setConsentMethod] = useState("verbal");
  const [consentChecked, setConsentChecked] = useState(false);

  // Buyer Portal State
  const [buyerRequirements, setBuyerRequirements] = useState([]);
  const [buyerCropName, setBuyerCropName] = useState("Tomato");
  const [buyerQuantity, setBuyerQuantity] = useState("100");
  const [buyerMaxPrice, setBuyerMaxPrice] = useState("1.20");
  const [buyerLocation, setBuyerLocation] = useState("Salem");
  const [buyerRequiredDate, setBuyerRequiredDate] = useState("2026-11-12");

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
        setQuantityCandidates(null); // clear any previous candidates
        // Call backend parse endpoint
        try {
          const parsed = await api.parseVoiceText(text);
          if (parsed.status === 'needs_confirmation' && Array.isArray(parsed.candidates) && parsed.candidates.length > 0) {
            // Ambiguous quantity: show candidate selection UI, do NOT auto-populate
            setQuantityCandidates(parsed.candidates);
          } else {
            setQuantityCandidates(null);
            if (parsed.crop_name) {
              const matchedCrop = CROPS.find(c => c.name.toLowerCase() === parsed.crop_name.toLowerCase());
              if (matchedCrop) setSelectedCrop(matchedCrop);
            }
            if (parsed.quantity) setQuantity(parsed.quantity.toString());
            if (parsed.expected_price) setExpectedPrice(parsed.expected_price.toString());
            if (parsed.location) setLocation(parsed.location);
          }
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

  }, [lang]);
  // Handle return from PayPal Sandbox after buyer approval or cancellation
  useEffect(() => {
    try {
      const currentUrl = new URL(window.location.href);
      const isSuccessReturn = currentUrl.pathname.includes('/checkout/success') || currentUrl.searchParams.has('PayerID');
      const isCancelReturn = currentUrl.pathname.includes('/checkout/cancel') || currentUrl.searchParams.get('cancel') === 'true';

      const orderIdParam = currentUrl.searchParams.get('order_id');
      const tokenParam = currentUrl.searchParams.get('token') || currentUrl.searchParams.get('paypal_order_id');

      if (isSuccessReturn || isCancelReturn) {
        // Clean URL to prevent duplicate actions on page refresh
        window.history.replaceState({}, '', window.location.origin + window.location.pathname.replace(/\/checkout\/(success|cancel)/, ''));
      }

      if (isCancelReturn) {
        sessionStorage.removeItem("hl_pending_payment");
        setPaymentBanner({
          type: 'info',
          message: t.paypal_payment_cancelled || "PayPal checkout was cancelled by the buyer. No funds were captured."
        });
        return;
      }

      if (isSuccessReturn) {
        const storedPending = JSON.parse(sessionStorage.getItem("hl_pending_payment") || "null");
        const targetOrderId = orderIdParam ? parseInt(orderIdParam, 10) : (storedPending ? storedPending.orderId : null);
        const targetPaypalId = tokenParam || (storedPending ? storedPending.paypalOrderId : null);

        if (!targetOrderId || !targetPaypalId) {
          setPaymentBanner({
            type: 'error',
            message: "Missing order or payment token in PayPal return. Cannot verify capture."
          });
          return;
        }

        // Prevent duplicate capture attempts and accidental automatic retries
        const captureKey = `hl_captured_${targetPaypalId}`;
        if (sessionStorage.getItem(captureKey) || captureAttemptedRef.current) {
          return;
        }

        captureAttemptedRef.current = true;
        sessionStorage.setItem(captureKey, "processing");

        executeCapture(targetOrderId, targetPaypalId, captureKey);
      }
    } catch (err) {
      console.error("Error inspecting PayPal return parameters", err);
    }
  }, []);

  const executeCapture = async (orderId, paypalOrderId, captureKey) => {
    setLoading(true);
    setPaymentBanner({
      type: 'loading',
      message: t.paypal_verifying_capture || "Buyer approved on PayPal. Securely verifying and capturing payment with backend..."
    });

    try {
      const paymentRecord = await api.capturePayPalOrder(orderId, paypalOrderId);

      // Do not treat returning to website as proof of payment - verify backend status
      if (paymentRecord && paymentRecord.status === 'completed') {
        sessionStorage.setItem(captureKey, "completed");
        sessionStorage.removeItem("hl_pending_payment");
        setPaymentBanner({
          type: 'success',
          message: `${t.paypal_payment_success || "Payment successfully captured and verified!"} (Capture ID: ${paymentRecord.paypal_capture_id || "verified"}). Order #${orderId} is now processing.`
        });
      } else {
        sessionStorage.setItem(captureKey, "failed");
        setPaymentBanner({
          type: 'error',
          message: `Payment verification failed: processor returned status '${paymentRecord?.status || "unverified"}'. Order remains unpaid.`
        });
      }
      await refreshData();
    } catch (err) {
      sessionStorage.setItem(captureKey, "failed");
      setPaymentBanner({
        type: 'error',
        message: `${t.paypal_payment_failed || "Payment capture failed"}: ${err.message || "Backend rejected capture"}. Order remains unpaid.`
      });
      await refreshData();
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    try {
      const [allListings, allOrders, logs, metrics, allReqs] = await Promise.all([
        api.fetchListings(),
        api.fetchOrders(),
        api.fetchAgentLogs(),
        api.fetchImpactMetrics(),
        api.fetchBuyerRequirements()
      ]);
      setListings(Array.isArray(allListings) ? allListings : []);
      setOrders(Array.isArray(allOrders) ? allOrders : []);
      setAgentLogs(Array.isArray(logs) ? logs : []);
      setImpactMetrics(metrics && typeof metrics === 'object' && !Array.isArray(metrics) ? metrics : null);
      setBuyerRequirements(Array.isArray(allReqs) ? allReqs : []);

      const safeListings = Array.isArray(allListings) ? allListings : [];
      if (safeListings.length > 0) {
        const first = safeListings[0];
        setActiveListing(first);
        const matchData = await api.fetchMatches(first.id);
        setMatches(Array.isArray(matchData) ? matchData : []);
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

  // Create Buyer Requirement
  const handlePostBuyerRequirement = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setLoading(true);
    try {
      await api.createBuyerRequirement({
        crop_name: buyerCropName,
        required_quantity: parseFloat(buyerQuantity) || 100,
        maximum_price: parseFloat(buyerMaxPrice) || 1.20,
        location: buyerLocation || "Salem",
        required_date: buyerRequiredDate || "2026-11-12"
      });
      await refreshData();
      alert(t.requirement_posted_success || "Procurement requirement successfully posted! AI agent will match with available farm produce.");
    } catch (err) {
      alert(err.message || "Failed to post requirement");
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
    setPaymentBanner({
      type: 'loading',
      message: t.paypal_redirecting || "Initiating PayPal Sandbox order..."
    });

    try {
      const payOrder = await api.createPayPalOrder(orderId);

      if (!payOrder || !payOrder.approval_url) {
        throw new Error("No approval URL returned by payment processor.");
      }

      // Check if mock mode
      if (payOrder.is_mock) {
        setPaymentBanner({
          type: 'loading',
          message: "Simulating mock payment verification..."
        });
        const completedPayment = await api.capturePayPalOrder(orderId, payOrder.paypal_order_id);
        if (completedPayment && completedPayment.status === 'completed') {
          setPaymentBanner({
            type: 'success',
            message: "Payment successfully verified and settled (Mock Mode)!"
          });
        }
        await refreshData();
        return;
      }

      // Real Sandbox mode: validate trusted PayPal sandbox checkout domain
      if (!isValidPayPalSandboxUrl(payOrder.approval_url)) {
        throw new Error(
          t.paypal_untrusted_url || "Security Error: Untrusted PayPal approval URL rejected. Must be on sandbox.paypal.com."
        );
      }

      // Store pending payment in sessionStorage to correlate upon return
      sessionStorage.setItem("hl_pending_payment", JSON.stringify({
        orderId,
        paypalOrderId: payOrder.paypal_order_id,
        status: "awaiting_buyer_approval",
        timestamp: Date.now()
      }));

      // Redirect buyer to PayPal Sandbox approval URL
      window.location.href = payOrder.approval_url;
    } catch (e) {
      console.error("PayPal order creation error:", e);
      setPaymentBanner({
        type: 'error',
        message: `${t.paypal_payment_failed || "Payment failed"}: ${e.message || "Processor error"}`
      });
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

  // Mobile OTP Auth Handlers
  useEffect(() => {
    let timer;
    if (cooldownSeconds > 0) {
      timer = setTimeout(() => setCooldownSeconds(c => c - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [cooldownSeconds]);

  const handleSendOTP = async () => {
    if (!loginPhone || !loginPhone.trim()) {
      setAuthError("Please enter a valid registered mobile number");
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    setAuthSuccess(null);
    try {
      const data = await api.requestOTP(loginPhone.trim());
      setOtpSent(true);
      setCooldownSeconds(30);
      if (data.demo_otp) {
        setDemoOtpDisplay(data.demo_otp);
      } else {
        setDemoOtpDisplay(null);
      }
    } catch (err) {
      setAuthError(err.message || "Failed to send OTP");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!loginOtp || loginOtp.trim().length !== 6) {
      setAuthError(t.invalid_otp_err || "Please enter a valid 6-digit OTP");
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    try {
      const data = await api.verifyOTP(loginPhone.trim(), loginOtp.trim());
      setCurrentUser(data.user);
      if (data.user?.role) {
        setRole(data.user.role);
      }
      setLoginOtp("");
      setDemoOtpDisplay(null);
      setAuthSuccess(t.login_success);
      setTimeout(() => setAuthSuccess(null), 4000);
      await refreshData();
    } catch (err) {
      setAuthError(err.message || "Failed to verify OTP");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setOtpSent(false);
    setLoginOtp("");
    setDemoOtpDisplay(null);
    setAuthError(null);
    setAuthSuccess(t.logout_success);
    setTimeout(() => setAuthSuccess(null), 3000);
  };

  const filteredCrops = ALL_CROPS.filter((crop) => {
    const matchesCategory = cropCategory === 'all' ||
      ALL_CROP_CATEGORIES.find(c => c.key === cropCategory)?.crops.some(c => c.name.toLowerCase() === crop.name.toLowerCase());
    const query = cropSearchQuery.trim().toLowerCase();
    const matchesSearch = !query ||
      crop.name.toLowerCase().includes(query) ||
      crop.ta.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });

  // 1. Session Verifying Screen (brief splash while checking token)
  if (isVerifyingSession) {
    return (
      <div className={`min-h-screen bg-gradient-to-br from-emerald-50 via-slate-50 to-green-50 flex flex-col items-center justify-center p-6 ${lang === 'ta' ? 'tamil-font' : ''}`}>
        <div className="w-16 h-16 rounded-2xl bg-agrigreen-600 flex items-center justify-center text-3xl shadow-lg shadow-agrigreen-600/30 mb-4 animate-pulse">
          🌱
        </div>
        <h2 className="text-xl font-bold text-slate-800">{t.app_title}</h2>
        <p className="text-xs text-slate-500 mt-2 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-agrigreen-600" />
          <span>{t.verifying_session}</span>
        </p>
      </div>
    );
  }

  // 2. Full-Page Login Screen (when not authenticated)
  if (!currentUser) {
    return (
      <div className={`min-h-screen bg-gradient-to-br from-emerald-50 via-slate-50 to-green-50 flex flex-col justify-between ${lang === 'ta' ? 'tamil-font' : ''}`}>
        {/* Top Navbar */}
        <header className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🌱</span>
            <div>
              <h1 className="text-xl font-black text-agrigreen-900 tracking-tight">{t.app_title}</h1>
              <p className="text-[11px] text-slate-500 hidden sm:block">{t.tagline}</p>
            </div>
          </div>
          {/* Language Selector */}
          <div className="flex bg-white/80 backdrop-blur-xs p-1 rounded-xl border border-slate-200/80 shadow-xs">
            <button
              onClick={() => setLang('ta')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${lang === 'ta' ? 'bg-agrigreen-700 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}
            >
              தமிழ்
            </button>
            <button
              onClick={() => setLang('en')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition cursor-pointer ${lang === 'en' ? 'bg-agrigreen-700 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}`}
            >
              English
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 my-auto">
          <div className="grid lg:grid-cols-12 gap-8 items-center">
            {/* Left Column: Platform Branding & Mission */}
            <div className="lg:col-span-5 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-agrigreen-100 text-agrigreen-800 text-xs font-bold border border-agrigreen-200 shadow-xs">
                <span>🌾</span>
                <span>Tamil Nadu Smallholder AgTech</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
                {t.welcome_back}
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                {t.mission}
              </p>

              {/* Key Highlights */}
              <div className="space-y-3 pt-2 text-left">
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-slate-200/60 shadow-xs">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-sm shrink-0">
                    🗣️
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">Tamil Voice Produce Listing</h4>
                    <p className="text-[11px] text-slate-500">Natural voice input with quantity & crop recognition</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-slate-200/60 shadow-xs">
                  <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-800 flex items-center justify-center font-bold text-sm shrink-0">
                    💳
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">PayPal Sandbox Escrow</h4>
                    <p className="text-[11px] text-slate-500">Verified buyer checkout & automated delivery release</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Full-Page Login Card */}
            <div className="lg:col-span-7">
              <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-200/80">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-xl bg-agrigreen-50 text-agrigreen-700 flex items-center justify-center text-xl border border-agrigreen-200">
                      📱
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-slate-900">{t.otp_login_title}</h3>
                      <p className="text-xs text-slate-500">{t.otp_login_desc}</p>
                    </div>
                  </div>
                  <ShieldCheck className="w-5 h-5 text-agrigreen-600 hidden sm:block" />
                </div>

                {/* Notifications */}
                {authError && (
                  <div className="my-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 font-medium flex items-start gap-2 animate-in fade-in">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
                    <span>{authError}</span>
                  </div>
                )}
                {authSuccess && (
                  <div className="my-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-medium flex items-center gap-2 animate-in fade-in">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                    <span>{authSuccess}</span>
                  </div>
                )}

                {/* Mobile Number Input */}
                <div className="mt-4 mb-4">
                  <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                    {t.phone_number_label}
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="tel"
                      value={loginPhone}
                      onChange={(e) => setLoginPhone(e.target.value)}
                      placeholder={t.phone_placeholder}
                      className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-semibold text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-agrigreen-500/20 focus:border-agrigreen-500 transition"
                    />
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      disabled={authLoading || cooldownSeconds > 0}
                      className="px-5 py-3 bg-agrigreen-700 hover:bg-agrigreen-800 disabled:bg-slate-300 text-white text-xs font-bold rounded-xl transition cursor-pointer whitespace-nowrap active:scale-95 shadow-sm"
                    >
                      {authLoading ? t.sending_otp : cooldownSeconds > 0 ? `${cooldownSeconds}s` : (otpSent ? t.resend_otp : t.send_otp)}
                    </button>
                  </div>
                </div>

                {/* Quick Demo Accounts Chips */}
                <div className="mb-5 p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
                  <p className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">
                    {t.demo_accounts_title}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => { setLoginPhone("+91-9876543210"); setAuthError(null); }}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition cursor-pointer flex items-center gap-1.5 ${loginPhone === '+91-9876543210' ? 'bg-agrigreen-100 text-agrigreen-900 border-agrigreen-300 shadow-xs' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'}`}
                    >
                      <span>👨‍🌾</span>
                      <span>Kumar (Farmer)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => { setLoginPhone("+91-9876543211"); setAuthError(null); }}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition cursor-pointer flex items-center gap-1.5 ${loginPhone === '+91-9876543211' ? 'bg-blue-100 text-blue-900 border-blue-300 shadow-xs' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'}`}
                    >
                      <span>🏢</span>
                      <span>Restaurant A (Buyer)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => { setLoginPhone("+91-9876543214"); setAuthError(null); }}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition cursor-pointer flex items-center gap-1.5 ${loginPhone === '+91-9876543214' ? 'bg-amber-100 text-amber-900 border-amber-300 shadow-xs' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'}`}
                    >
                      <span>🤝</span>
                      <span>Selvi (Operator)</span>
                    </button>
                  </div>
                </div>

                {/* Demo OTP Box (Displayed only when backend returns demo_otp) */}
                {demoOtpDisplay && (
                  <div className="mb-5 p-4 bg-amber-50 border-2 border-amber-300 rounded-2xl animate-in fade-in">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                        <Sparkles className="w-4 h-4 text-amber-600" />
                        <span>{t.demo_otp_notice}</span>
                      </span>
                      <span className="text-[10px] font-bold bg-amber-200 text-amber-900 px-2 py-0.5 rounded-full uppercase">Demo</span>
                    </div>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-amber-200/80">
                      <div>
                        <span className="text-[11px] text-amber-800 block">{t.demo_otp_code}:</span>
                        <span className="text-2xl font-mono font-black tracking-widest text-amber-950">{demoOtpDisplay}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setLoginOtp(demoOtpDisplay)}
                        className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-xl transition shadow-xs active:scale-95 cursor-pointer"
                      >
                        Auto-fill OTP
                      </button>
                    </div>
                  </div>
                )}

                {/* Six-Digit OTP Input */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                      {t.otp_label}
                    </label>
                    {otpSent && (
                      <span className="text-[11px] text-agrigreen-700 font-semibold">
                        ✓ OTP requested
                      </span>
                    )}
                  </div>
                  <input
                    type="text"
                    maxLength={6}
                    value={loginOtp}
                    onChange={(e) => setLoginOtp(e.target.value.replace(/\D/g, ''))}
                    placeholder="• • • • • •"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3.5 text-center text-2xl font-mono font-black tracking-[0.4em] text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-agrigreen-500/20 focus:border-agrigreen-500 transition"
                  />
                </div>

                {/* Verify Button */}
                <button
                  type="button"
                  onClick={handleVerifyOTP}
                  disabled={authLoading || !loginOtp || loginOtp.length !== 6}
                  className="w-full py-4 bg-agrigreen-700 hover:bg-agrigreen-800 disabled:bg-slate-300 text-white text-sm font-bold rounded-2xl shadow-lg shadow-agrigreen-700/20 transition active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {authLoading ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5" />
                  )}
                  <span>{authLoading ? t.verifying_otp : t.verify_otp}</span>
                </button>

                <p className="text-[11px] text-center text-slate-400 mt-4 flex items-center justify-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                  <span>{t.secure_login_badge}</span>
                </p>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="w-full max-w-7xl mx-auto px-4 py-4 text-center text-[11px] text-slate-400 border-t border-slate-200/60">
          HarvestLink AI • PayPal AI Hackathon 2026 • Verified Smallholder Produce & Escrow Settlement
        </footer>
      </div>
    );
  }

  // 3. Authenticated Dashboard
  return (
    <div className={`min-h-screen bg-slate-50 text-slate-900 pb-16 ${lang === 'ta' ? 'tamil-font' : ''}`}>

      {/* PayPal Environment Status Banner */}
      <div className={`font-medium px-4 py-2 text-center text-xs md:text-sm flex items-center justify-center gap-2 ${paypalMode === 'sandbox'
        ? 'bg-blue-100 text-blue-900'
        : paypalMode === 'mock'
          ? 'bg-amber-500 text-slate-950'
          : 'bg-slate-200 text-slate-800'
        }`}>
        <AlertTriangle className="w-4 h-4" />
        <span>
          {paypalMode === 'sandbox'
            ? 'PAYPAL SANDBOX MODE — Test payments only (USD). No real money.'
            : paypalMode === 'mock'
              ? 'MOCK MODE — Simulated payments only. No real PayPal transaction.'
              : 'PAYPAL STATUS UNKNOWN — Backend connection could not be verified.'}
        </span>
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

            {/* User Profile & Logout */}
            <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-bold text-slate-800 leading-none">{currentUser.name}</p>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">{currentUser.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-xs bg-slate-100 hover:bg-red-50 hover:text-red-700 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-semibold transition cursor-pointer"
              >
                {t.logout}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Auth Notification Banner */}
      {authSuccess && (
        <div className="bg-emerald-600 text-white px-4 py-2 text-center text-xs font-semibold flex items-center justify-center gap-2 shadow-xs">
          <CheckCircle2 className="w-4 h-4" />
          <span>{authSuccess}</span>
        </div>
      )}

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

      {/* PayPal Sandbox Payment Status Banner */}
      {paymentBanner && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className={`p-4 rounded-xl border flex items-center justify-between ${paymentBanner.type === 'success' ? 'bg-emerald-50 border-emerald-300 text-emerald-900' :
            paymentBanner.type === 'error' ? 'bg-rose-50 border-rose-300 text-rose-900' :
              paymentBanner.type === 'loading' ? 'bg-blue-50 border-blue-300 text-blue-900' :
                'bg-amber-50 border-amber-300 text-amber-900'
            }`}>
            <div className="flex items-center gap-2.5 text-sm font-medium">
              {paymentBanner.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />}
              {paymentBanner.type === 'error' && <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />}
              {paymentBanner.type === 'loading' && <RefreshCw className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />}
              {paymentBanner.type === 'info' && <Clock className="w-5 h-5 text-amber-600 flex-shrink-0" />}
              <span>{paymentBanner.message}</span>
            </div>
            <button
              onClick={() => setPaymentBanner(null)}
              className="text-xs font-semibold underline ml-4 hover:opacity-80 flex-shrink-0"
            >
              Dismiss
            </button>
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

        {/* Left Column: Input Form (Buyer vs Farmer / Operator) */}
        {role === 'buyer' ? (
          <section className="lg:col-span-5 space-y-6">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <span>🏢</span>
                  <span>{t.buyer_portal_title}</span>
                </h2>
                <span className="text-xs bg-blue-100 text-blue-700 px-2.5 py-1 rounded-full font-medium">
                  Buyer Mode
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-5">{t.buyer_portal_desc}</p>

              {/* Picture-based Crop Selection (6 Crops) */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wider">{t.crop}</label>
                <div className="grid grid-cols-3 gap-2 mb-2">
                  {QUICK_BUYER_CROPS.map((crop) => (
                    <button
                      key={crop.name}
                      type="button"
                      onClick={() => {
                        setBuyerCropName(crop.name);
                        setBuyerMaxPrice((crop.defaultExpected * 1.2).toFixed(2));
                      }}
                      className={`p-2.5 rounded-xl border text-center transition flex flex-col items-center gap-1 ${buyerCropName.toLowerCase() === crop.name.toLowerCase()
                        ? 'border-blue-600 bg-blue-50 text-blue-900 font-bold ring-2 ring-blue-500/20'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                        }`}
                    >
                      <span className="text-2xl">{crop.icon}</span>
                      <span className="text-xs">{lang === 'ta' ? crop.ta : crop.name}</span>
                    </button>
                  ))}
                </div>
                <input
                  type="text"
                  value={buyerCropName}
                  onChange={(e) => setBuyerCropName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs font-semibold text-slate-700"
                  placeholder="Or enter crop name..."
                />
              </div>

              {/* Form Fields */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">{t.quantity_kg}</label>
                  <input
                    type="number"
                    value={buyerQuantity}
                    onChange={(e) => setBuyerQuantity(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">{t.max_purchase_price}</label>
                  <input
                    type="number"
                    step="0.05"
                    value={buyerMaxPrice}
                    onChange={(e) => setBuyerMaxPrice(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                    placeholder="1.20"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-5">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">{t.location}</label>
                  <input
                    type="text"
                    value={buyerLocation}
                    onChange={(e) => setBuyerLocation(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                    placeholder="Salem"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">{t.required_date}</label>
                  <input
                    type="date"
                    value={buyerRequiredDate}
                    onChange={(e) => setBuyerRequiredDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm font-semibold"
                  />
                </div>
              </div>

              {/* Post Button */}
              <button
                onClick={handlePostBuyerRequirement}
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md transition active:scale-95 flex items-center justify-center gap-2"
              >
                <span>🏢</span>
                <span>{t.post_requirement}</span>
              </button>
            </div>

            {/* Active Demands Card */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
                <span>📋</span>
                <span>{t.buyer_demands_title}</span>
                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-normal">
                  {buyerRequirements.length}
                </span>
              </h3>
              {buyerRequirements.length === 0 ? (
                <p className="text-xs text-slate-400 py-3 text-center">
                  No procurement requirements posted yet.
                </p>
              ) : (
                <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                  {buyerRequirements.map((req) => (
                    <div key={req.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-bold text-slate-800">
                          {req.crop_name} • {req.required_quantity} kg
                        </p>
                        <p className="text-xs text-slate-500">
                          Max: ${parseFloat(req.maximum_price).toFixed(2)}/kg • {req.location || 'Salem'} • {req.required_date || 'ASAP'}
                        </p>
                        {req.buyer_name && (
                          <p className="text-[11px] text-slate-400 font-medium">By: {req.buyer_name}</p>
                        )}
                      </div>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 capitalize">
                        {req.status || 'open'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        ) : (
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
                  className={`w-20 h-20 rounded-full mx-auto flex items-center justify-center transition shadow-md active:scale-95 ${isListening ? 'bg-red-500 animate-pulse text-white' : 'bg-agrigreen-600 hover:bg-agrigreen-700 text-white'
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

                {/* needs_confirmation: show candidate quantity buttons, never auto-populate */}
                {quantityCandidates && (
                  <div className="mt-3 p-3 bg-amber-50 border border-amber-300 rounded-lg text-left">
                    <p className="text-xs font-semibold text-amber-900 mb-2">
                      {lang === 'ta'
                        ? 'அளவு தெளிவாக புரியவில்லை. சரியான அளவை தேர்ந்தெடுக்கவும்:'
                        : 'Quantity was ambiguous. Please select the correct amount:'}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {quantityCandidates.map((cand) => (
                        <button
                          key={cand}
                          type="button"
                          onClick={() => {
                            setQuantity(cand.toString());
                            setQuantityCandidates(null);
                          }}
                          className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-lg transition active:scale-95"
                        >
                          {cand} kg
                        </button>
                      ))}
                      <button
                        type="button"
                        onClick={() => setQuantityCandidates(null)}
                        className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs rounded-lg transition"
                      >
                        {lang === 'ta' ? 'ரத்து செய்' : 'Cancel'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Crop Selection with Category Tabs, Search Box & Large Tap Targets */}
              <div className="mb-5">
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">{t.crop}</label>
                  {selectedCrop && (
                    <span className="text-xs bg-agrigreen-100 text-agrigreen-900 font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1.5 border border-agrigreen-200">
                      <span>{selectedCrop.icon}</span>
                      <span>{lang === 'ta' ? selectedCrop.ta : selectedCrop.name}</span>
                      <span className="text-[10px] text-agrigreen-700 bg-white/70 px-1 rounded font-normal">({t.crop_selected_msg})</span>
                    </span>
                  )}
                </div>

                {/* Search Box */}
                <div className="relative mb-2.5">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={cropSearchQuery}
                    onChange={(e) => setCropSearchQuery(e.target.value)}
                    placeholder={t.crop_search_placeholder}
                    className="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-agrigreen-500/20 focus:border-agrigreen-500 transition"
                  />
                  {cropSearchQuery && (
                    <button
                      type="button"
                      onClick={() => setCropSearchQuery('')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Category Tabs */}
                <div className="flex gap-1.5 overflow-x-auto pb-1 mb-2.5 scrollbar-thin">
                  <button
                    type="button"
                    onClick={() => setCropCategory('all')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition cursor-pointer ${cropCategory === 'all'
                      ? 'bg-agrigreen-700 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                  >
                    {t.crop_category_all}
                  </button>
                  {ALL_CROP_CATEGORIES.map((cat) => (
                    <button
                      key={cat.key}
                      type="button"
                      onClick={() => setCropCategory(cat.key)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition cursor-pointer ${cropCategory === cat.key
                        ? 'bg-agrigreen-700 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                    >
                      {t[cat.labelKey] || cat.key}
                    </button>
                  ))}
                </div>

                {/* Crop Grid with Large Tap Targets & Selected Highlight */}
                {filteredCrops.length === 0 ? (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center text-xs text-slate-500">
                    {t.no_crops_found}
                  </div>
                ) : (
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-64 overflow-y-auto p-1.5 border border-slate-200 rounded-xl bg-slate-50/50">
                    {filteredCrops.map((crop) => {
                      const isSelected = selectedCrop?.name.toLowerCase() === crop.name.toLowerCase();
                      return (
                        <button
                          key={crop.name}
                          type="button"
                          onClick={() => {
                            setSelectedCrop(crop);
                            setExpectedPrice(crop.defaultExpected.toFixed(2));
                            setMinimumPrice(crop.defaultMin.toFixed(2));
                          }}
                          className={`min-h-[72px] p-2 rounded-xl border text-center transition flex flex-col items-center justify-center gap-0.5 cursor-pointer active:scale-95 ${isSelected
                            ? 'border-2 border-agrigreen-600 bg-agrigreen-50 text-agrigreen-950 font-bold ring-2 ring-agrigreen-500/30 shadow-sm'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-agrigreen-300 hover:bg-slate-50'
                            }`}
                        >
                          <span className="text-2xl leading-none">{crop.icon}</span>
                          <span className="text-xs font-semibold leading-tight line-clamp-1">
                            {lang === 'ta' ? crop.ta : crop.name}
                          </span>
                          <span className="text-[10px] text-slate-400 leading-none">
                            {lang === 'ta' ? crop.name : crop.ta}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
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
        )}

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
                      ℹ️ {m.match_reason || 'Reason not available'}
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
                      <span className={`inline-block mt-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${o.payment_status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
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
