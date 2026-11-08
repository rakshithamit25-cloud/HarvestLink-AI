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

  // Orders
  fetchOrders: async () => {
    const res = await fetch(`${API_BASE}/orders`);
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
    const res = await fetch(`${API_BASE}/payments/create-order/${orderId}`, {
      method: "POST"
    });
    return res.json();
  },
  capturePayPalOrder: async (orderId, paypalOrderId) => {
    const res = await fetch(`${API_BASE}/payments/capture/${orderId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paypal_order_id: paypalOrderId })
    });
    return res.json();
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
    return res.json();
  },
  fetchImpactMetrics: async () => {
    const res = await fetch(`${API_BASE}/impact/metrics`);
    return res.json();
  }
};
