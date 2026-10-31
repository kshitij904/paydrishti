// PayDrishti checkout logic.
// Flow: create order -> (PayPal approval) -> risk check -> interstitial? -> capture.
// Works in MOCK mode (no PayPal keys) and LIVE mode (real sandbox buttons).

let CONFIG = { mode: "mock", client_id: "", currency: "USD" };
let currentOrderId = null;

const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

function setStatus(kind, html) {
  const el = $("status");
  el.className = "status " + kind;
  el.innerHTML = html;
  el.hidden = false;
}

function selectedPayee() { return $("payee").value; }
function selectedLabel() {
  const p = PAYEES.find((x) => x.id === selectedPayee());
  return p ? p.label : "this payee";
}
function amount() { return parseFloat($("amount").value || "0"); }

// ---------- risk + capture ----------
async function afterApproval(orderId) {
  currentOrderId = orderId;
  const risk = await api("/api/risk-check", { order_id: orderId });
  if (risk.show_interstitial) {
    showInterstitial(risk);
  } else {
    await doCapture();  // low risk -> straight through
  }
}

async function doCapture() {
  try {
    const r = await api("/api/capture", { order_id: currentOrderId });
    hideInterstitial();
    setStatus("ok", `✓ Payment of $${Number(r.amount ?? amount()).toFixed(2)} completed` +
      (r.mode === "mock" ? " <em>(mock)</em>" : " via PayPal sandbox") + ".");
  } catch (e) {
    setStatus("err", "Payment error: " + e.message);
  }
}

// ---------- interstitial ----------
function showInterstitial(risk) {
  $("score-label").textContent = `risk ${risk.score}/100`;
  $("meter-fill").style.width = risk.score + "%";
  const ul = $("reasons");
  ul.innerHTML = "";
  (risk.reasons || []).slice(0, 4).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r.text;
    ul.appendChild(li);
  });
  $("warn-text").textContent = risk.warning_text || "";
  $("overlay").hidden = false;
}

function hideInterstitial() { $("overlay").hidden = true; }

$("btn-cancel").onclick = () => {
  hideInterstitial();
  setStatus("cancel", "Payment cancelled. Good call — verify the recipient before sending money.");
  currentOrderId = null;
};
$("btn-proceed").onclick = () => doCapture();

// ---------- payee note ----------
let PAYEES = [];
function updateNote() {
  const p = PAYEES.find((x) => x.id === selectedPayee());
  $("payee-note").textContent = p ? p.note : "";
}

// ---------- mock pay button ----------
async function mockPay() {
  $("status").hidden = true;
  try {
    const order = await api("/api/create-order",
      { payee_id: selectedPayee(), amount: amount(), payee_label: selectedLabel() });
    await afterApproval(order.id);
  } catch (e) {
    setStatus("err", "Could not start payment: " + e.message);
  }
}

// ---------- live PayPal buttons ----------
function loadPayPalButtons() {
  const s = document.createElement("script");
  s.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(CONFIG.client_id)}` +
          `&currency=${CONFIG.currency}&intent=capture`;
  s.onload = () => {
    window.paypal.Buttons({
      createOrder: async () => {
        $("status").hidden = true;
        const order = await api("/api/create-order",
          { payee_id: selectedPayee(), amount: amount(), payee_label: selectedLabel() });
        return order.id;
      },
      onApprove: async (data) => { await afterApproval(data.orderID); },
      onError: (err) => setStatus("err", "PayPal error: " + err),
    }).render("#paypal-button-container");
  };
  s.onerror = () => setStatus("err", "Could not load PayPal SDK — check your client ID.");
  document.head.appendChild(s);
}

// ---------- init ----------
(async function init() {
  try {
    CONFIG = await api("/api/config");
  } catch (e) {
    setStatus("err", "Backend not reachable. Is the server running?");
    return;
  }
  $("mode-badge").textContent = CONFIG.mode === "mock" ? "mock mode" : "sandbox";

  PAYEES = await api("/api/payees");
  const sel = $("payee");
  PAYEES.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.id; o.textContent = p.label;
    sel.appendChild(o);
  });
  sel.onchange = updateNote;
  updateNote();

  if (CONFIG.mode === "live" && CONFIG.client_id) {
    loadPayPalButtons();
  } else {
    const b = $("mock-pay");
    b.hidden = false;
    b.onclick = mockPay;
  }
})();
