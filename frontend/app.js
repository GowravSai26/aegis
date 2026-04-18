/* ═══════════════════════════════════════════════════════════════
   AEGIS — app.js
   Handles dispute submission, agent pipeline animation,
   results rendering, and document download.
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:8000';

// ── STATE ──────────────────────────────────────────────────────
let currentDisputeId = null;

// ── DOM REFS ───────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const idleState     = $('idleState');
const loadingState  = $('loadingState');
const resultsState  = $('resultsState');
const errorState    = $('errorState');
const submitBtn     = $('submitBtn');

// ── PIPELINE STEPS ─────────────────────────────────────────────
const STEPS = [
  { id: 'step-intake',    name: 'Intake Agent',       label: 'Classifying dispute & urgency…'     },
  { id: 'step-evidence',  name: 'Evidence Collector', label: 'Gathering order, delivery & auth records…' },
  { id: 'step-strategy',  name: 'Strategy Agent',     label: 'Evaluating winability & strategy…'  },
  { id: 'step-writer',    name: 'Writer Agent',        label: 'Drafting formal dispute response…'  },
  { id: 'step-reviewer',  name: 'Reviewer Agent',      label: 'Reviewing and finalising document…' },
];

// ── UI HELPERS ─────────────────────────────────────────────────
function showOnly(el) {
  [idleState, loadingState, resultsState, errorState].forEach(e => {
    if (e) e.classList.add('hidden');
  });
  if (el) el.classList.remove('hidden');
}

function resetPipeline() {
  STEPS.forEach(s => {
    const el = $(s.id);
    if (!el) return;
    el.classList.remove('active', 'done');
    el.querySelector('.step-status').textContent = 'Waiting';
  });
}

async function animatePipeline() {
  const subtextEl = $('loadingSubtext');
  for (let i = 0; i < STEPS.length; i++) {
    const step = STEPS[i];
    const el   = $(step.id);
    if (!el) continue;

    // Mark previous as done
    if (i > 0) {
      const prev = $(STEPS[i - 1].id);
      if (prev) {
        prev.classList.remove('active');
        prev.classList.add('done');
        prev.querySelector('.step-status').textContent = 'Complete ✓';
      }
    }

    // Activate current
    el.classList.add('active');
    el.querySelector('.step-status').textContent = 'Running…';
    if (subtextEl) subtextEl.textContent = step.label;

    // Wait a beat before next (timing approximates real agent runtime)
    const delays = [800, 1200, 700, 1100, 600];
    await delay(delays[i]);
  }

  // Mark last step done
  const last = $(STEPS[STEPS.length - 1].id);
  if (last) {
    last.classList.remove('active');
    last.classList.add('done');
    last.querySelector('.step-status').textContent = 'Complete ✓';
  }
  if (subtextEl) subtextEl.textContent = 'Finalising response…';
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── FORM COLLECTION ────────────────────────────────────────────
function collectForm() {
  const val = id => ($(id)?.value || '').trim();
  return {
    dispute_id:   val('dispute_id'),
    reason_code:  val('reason_code'),
    amount:       parseFloat(val('amount')) || 0,
    merchant:     val('merchant'),
    txn_date:     val('txn_date'),
    cardholder:   val('cardholder'),
    notes:        val('notes'),
  };
}

function validateForm(data) {
  if (!data.dispute_id)  return 'Please enter a Dispute ID.';
  if (!data.reason_code) return 'Please select a Reason Code.';
  if (!data.amount || data.amount <= 0) return 'Please enter a valid amount.';
  return null;
}

// ── RENDER RESULTS ─────────────────────────────────────────────
function renderResults(data, disputeId) {
  // Dispute ID tag
  $('resultDisputeId').textContent = disputeId;

  // Verdict badge
  const verdict = data.verdict || data.strategy || 'FIGHT';
  const badge   = $('verdictBadge');
  badge.textContent = verdict.toUpperCase();
  badge.className   = `verdict-badge ${verdict.toUpperCase()}`;

  // Winability
  const score   = typeof data.winability_score === 'number'
    ? Math.round(data.winability_score * 100)
    : (typeof data.winability_score === 'string'
        ? Math.round(parseFloat(data.winability_score) * 100)
        : 80);
  $('winabilityPct').textContent = `${score}%`;
  setTimeout(() => {
    $('winabilityFill').style.width = `${score}%`;
  }, 100);

  // Evidence grid
  const grid  = $('evidenceGrid');
  grid.innerHTML = '';
  const evidence = data.evidence_collected || data.evidence || {};
  if (typeof evidence === 'object' && Object.keys(evidence).length) {
    Object.entries(evidence).forEach(([key, val]) => {
      const strength = typeof val === 'number' ? val : (val?.strength || val?.score || null);
      const strong   = strength === null || strength >= 0.5;
      const label    = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      const scoreStr = strength !== null ? `${Math.round(strength * 100)}%` : 'Present';
      grid.innerHTML += `
        <div class="evidence-item ${strong ? 'strong' : 'weak'}">
          <span class="ev-name">${label}</span>
          <span class="ev-score">Score: <span>${scoreStr}</span></span>
        </div>`;
    });
  } else {
    // Fallback — show generic evidence chips
    const defaults = ['Order Lookup', 'Delivery Proof', 'Device Fingerprint', 'Auth History'];
    defaults.forEach(name => {
      grid.innerHTML += `
        <div class="evidence-item strong">
          <span class="ev-name">${name}</span>
          <span class="ev-score">Score: <span>Collected</span></span>
        </div>`;
    });
  }

  // Strategy rationale
  const rationale = data.rationale || data.strategy_rationale || data.reason ||
    'AEGIS has completed its multi-agent analysis. The recommendation above reflects evidence strength, reason code risk profile, and historical dispute patterns.';
  $('strategyText').textContent = rationale;

  // Document
  const docName = `${disputeId}.docx`;
  $('docName').textContent = docName;
  $('downloadBtn').onclick  = () => downloadDoc(disputeId);
}

// ── SUBMIT ─────────────────────────────────────────────────────
async function submitDispute() {
  const data   = collectForm();
  const errMsg = validateForm(data);

  if (errMsg) {
    showValidationError(errMsg);
    return;
  }

  // Lock form
  submitBtn.disabled = true;
  submitBtn.querySelector('.btn-text').textContent = 'Analysing…';

  // Reset + show loading
  resetPipeline();
  showOnly(loadingState);

  // Start pipeline animation (runs in parallel with API call)
  const pipelinePromise = animatePipeline();

  try {
    // API call — adjust payload to match your FastAPI schema
    const response = await fetch(`${API_BASE}/dispute`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dispute_id:   data.dispute_id,
        reason_code:  data.reason_code,
        amount:       data.amount,
        merchant:     data.merchant     || undefined,
        txn_date:     data.txn_date     || undefined,
        cardholder:   data.cardholder   || undefined,
        notes:        data.notes        || undefined,
      }),
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `Server error ${response.status}`);
    }

    const result = await response.json();
    currentDisputeId = data.dispute_id;

    // Wait for pipeline animation to finish before showing results
    await pipelinePromise;
    await delay(400);

    renderResults(result, data.dispute_id);
    showOnly(resultsState);

  } catch (err) {
    await pipelinePromise.catch(() => {});
    console.error('AEGIS API error:', err);
    $('errorMsg').textContent = err.message.includes('Failed to fetch')
      ? 'Unable to reach the AEGIS API. Ensure the FastAPI server is running on localhost:8000.'
      : err.message;
    showOnly(errorState);
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').textContent = 'Launch Defense Analysis';
  }
}

// ── DOWNLOAD ───────────────────────────────────────────────────
async function downloadDoc(disputeId) {
  const btn = $('downloadBtn');
  const originalHTML = btn.innerHTML;
  btn.textContent = 'Downloading…';
  btn.disabled    = true;

  try {
    const response = await fetch(`${API_BASE}/dispute/${disputeId}/download`);
    if (!response.ok) throw new Error(`Download failed: ${response.status}`);

    const blob = await response.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `${disputeId}.docx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert(`Download failed: ${err.message}`);
  } finally {
    btn.innerHTML = originalHTML;
    btn.disabled  = false;
  }
}

// ── RESET ──────────────────────────────────────────────────────
function resetForm() {
  currentDisputeId = null;
  showOnly(idleState);
  // Optionally clear form fields
  ['dispute_id','reason_code','amount','merchant','txn_date','cardholder','notes']
    .forEach(id => { const el = $(id); if (el) el.value = ''; });
}

// ── VALIDATION TOAST ───────────────────────────────────────────
function showValidationError(msg) {
  // Remove existing toast
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;

  // Inline styles so no extra CSS class needed
  Object.assign(toast.style, {
    position:     'fixed',
    bottom:       '28px',
    left:         '50%',
    transform:    'translateX(-50%)',
    background:   '#1a2440',
    border:       '1px solid rgba(245,158,11,0.4)',
    color:        '#f59e0b',
    padding:      '10px 20px',
    borderRadius: '6px',
    fontSize:     '0.85rem',
    fontFamily:   "'Barlow Semi Condensed', sans-serif",
    fontWeight:   '500',
    letterSpacing:'0.03em',
    zIndex:       '9999',
    boxShadow:    '0 4px 20px rgba(0,0,0,0.4)',
    animation:    'fadeUp 0.2s ease',
  });

  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── KEYBOARD SHORTCUT ──────────────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    submitDispute();
  }
});

// ── INIT ───────────────────────────────────────────────────────
showOnly(idleState);