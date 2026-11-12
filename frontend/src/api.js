const API_BASE = "http://localhost:8000/api";

export const api = {
  // Demo
  runDemoScenario: async () => {
    const res = await fetch(`${API_BASE}/demo/run-scenario`, { method: "POST" });
    return res.json();
  },
  resetDemoData: async () => {
    const res = await fetch(`${API_BASE}/demo/reset`, { method: "POST" });
    return res.json();
  },

  // NLP Voice/Text Parse
  parseVoiceText: async (text) => {
    const res = await fetch(`${API_BASE}/listings/parse-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    return res.json();
  },

  // Listings
  fetchListings: async () => {
    const res = await fetch(`${API_BASE}/listings`);
    if (!res.ok) return [];
    return res.json();
  },
  createListing: async (listingData) => {
    const res = await fetch(`${API_BASE}/listings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(listingData)
    });
    return res.json();
  },

  // Matching
  runMatching: async (listingId, mode = "rule-based") => {
    const res = await fetch(`${API_BASE}/matching/run/${listingId}?mode=${mode}`, {
      method: "POST"
    });
    return res.json();
  },
  fetchMatches: async (listingId) => {
    const res = await fetch(`${API_BASE}/matching/results/${listingId}`);
    return res.json();
  },
  approveFarmerMatch: async (matchId, payload = {}) => {
    const res = await fetch(`${API_BASE}/matching/${matchId}/approve-farmer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return res.json();
  },
  approveBuyerMatch: async (matchId) => {
    const res = await fetch(`${API_BASE}/matching/${matchId}/approve-buyer`, {
      method: "POST"
    });
    return res.json();
  },
  rejectMatch: async (matchId, reason) => {
    const res = await fetch(`${API_BASE}/matching/${matchId}/reject?reason=${encodeURIComponent(reason || "")}`, {
      method: "POST"
    });
    return res.json();
  },

  // Buyers
  fetchBuyerRequirements: async () => {
    const res = await fetch(`${API_BASE}/buyers/requirements`);
    if (!res.ok) return [];
    return res.json();
  },
  createBuyerRequirement: async (reqData) => {
    const token = await api.ensureBuyerAuth();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/buyers/requirements`, {
      method: "POST",
      headers,
      body: JSON.stringify(reqData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create requirement");
    }
    return res.json();
  },

  // Auth
  login: async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      throw new Error("Authentication failed");
    }
    const data = await res.json();
    if (data.access_token) {
      sessionStorage.setItem("hl_buyer_token", data.access_token);
      sessionStorage.setItem("hl_auth_token", data.access_token);
      if (data.user) {
        sessionStorage.setItem("hl_user", JSON.stringify(data.user));
      }
    }
    return data;
  },

  // Mobile OTP Authentication
  requestOTP: async (phone) => {
    const res = await fetch(`${API_BASE}/auth/otp/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to request OTP");
    }
    return data;
  },

  verifyOTP: async (phone, otp) => {
    const res = await fetch(`${API_BASE}/auth/otp/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, otp })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to verify OTP");
    }
    if (data.access_token) {
      sessionStorage.setItem("hl_buyer_token", data.access_token);
      sessionStorage.setItem("hl_auth_token", data.access_token);
      if (data.user) {
        sessionStorage.setItem("hl_user", JSON.stringify(data.user));
      }
    }
    return data;
  },

  logout: () => {
    sessionStorage.removeItem("hl_buyer_token");
    sessionStorage.removeItem("hl_auth_token");
    sessionStorage.removeItem("hl_user");
  },

  getAuthToken: () => {
    return sessionStorage.getItem("hl_auth_token") || sessionStorage.getItem("hl_buyer_token") || null;
  },

  getStoredUser: () => {
    try {
      const u = sessionStorage.getItem("hl_user");
      return u ? JSON.parse(u) : null;
    } catch (e) {
      return null;
    }
  },

  validateSession: async () => {
    const token = api.getAuthToken();
    if (!token) {
      api.logout();
      return null;
    }
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) {
        api.logout();
        return null;
      }
      const user = await res.json();
      sessionStorage.setItem("hl_user", JSON.stringify(user));
      return user;
    } catch (e) {
      console.warn("Session validation check failed", e);
      api.logout();
      return null;
    }
  },

  ensureBuyerAuth: async () => {
    // Return active session token. Never automatically log in visitors using seeded credentials!
    return api.getAuthToken();
  },

  // Orders
  fetchOrders: async () => {
    const token = await api.ensureBuyerAuth();
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/orders`, { headers });
    if (!res.ok) return [];
    return res.json();
  },
  confirmDelivery: async (orderId, payload = {}) => {
    const res = await fetch(`${API_BASE}/orders/${orderId}/confirm-delivery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  // Payments
  createPayPalOrder: async (orderId) => {
    const token = await api.ensureBuyerAuth();
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/payments/create-order/${orderId}`, {
      method: "POST",
      headers
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `PayPal order creation failed (${res.status})`);
    }
    return data;
  },
  capturePayPalOrder: async (orderId, paypalOrderId) => {
    const token = await api.ensureBuyerAuth();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/payments/capture/${orderId}`, {
      method: "POST",
      headers,
      body: JSON.stringify({ paypal_order_id: paypalOrderId })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `PayPal capture failed (${res.status})`);
    }
    return data;
  },

  // Operator
  createOperatorListing: async (payload) => {
    const res = await fetch(`${API_BASE}/operator/listings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return res.json();
  },
  fetchAuditLogs: async () => {
    const res = await fetch(`${API_BASE}/operator/audit-logs`);
    return res.json();
  },

  // Logs & Metrics
  fetchAgentLogs: async () => {
    const res = await fetch(`${API_BASE}/logs/agent?limit=20`);
    if (!res.ok) return [];
    return res.json();
  },

  fetchImpactMetrics: async () => {
    const res = await fetch(`${API_BASE}/impact/metrics`);
    if (!res.ok) return null;
    return res.json();
  },

  // PayPal configuration
  fetchPayPalConfig: async () => {
    const res = await fetch("http://localhost:8000/");
    if (!res.ok) throw new Error("Could not fetch PayPal configuration");
    return res.json();
  }
};
