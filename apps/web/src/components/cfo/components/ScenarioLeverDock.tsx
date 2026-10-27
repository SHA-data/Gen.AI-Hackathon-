import React, { useState, useMemo } from 'react';

export interface ScenarioChangePayload {
  lever: string;
  op: 'set' | 'add' | 'multiply';
  value: number | string;
  start_date?: string;
  params: Record<string, any>;
  is_assumption?: boolean;
}

export interface ScenarioLeverDockProps {
  onRunScenario?: (changes: ScenarioChangePayload[], scenarioName: string) => void | Promise<void>;
  onResetBaseline?: () => void;
  isLoading?: boolean;
  defaultClient?: string;
}

export const ScenarioLeverDock: React.FC<ScenarioLeverDockProps> = ({
  onRunScenario,
  onResetBaseline,
  isLoading = false,
  defaultClient = 'Apex Systems',
}) => {
  // Lever States
  const [hireCount, setHireCount] = useState<number>(2);
  const [hireMonthlyCost, setHireMonthlyCost] = useState<number>(7000);
  const [hireActive, setHireActive] = useState<boolean>(true);

  const [delayClient, setDelayClient] = useState<string>(defaultClient);
  const [delayDays, setDelayDays] = useState<number>(30);
  const [delayActive, setDelayActive] = useState<boolean>(true);

  const [depositPct, setDepositPct] = useState<number>(0);
  const [depositActive, setDepositActive] = useState<boolean>(false);

  const [paymentTermsDays, setPaymentTermsDays] = useState<number>(0);
  const [termsActive, setTermsActive] = useState<boolean>(false);

  const [lostClientName, setLostClientName] = useState<string>('Apex Systems');
  const [lostClientActive, setLostClientActive] = useState<boolean>(false);

  const [priceChangePct, setPriceChangePct] = useState<number>(0);
  const [priceActive, setPriceActive] = useState<boolean>(false);

  const [revChangePct, setRevChangePct] = useState<number>(0);
  const [revActive, setRevActive] = useState<boolean>(false);

  const [expenseAmt, setExpenseAmt] = useState<number>(3500);
  const [expenseCadence, setExpenseCadence] = useState<'monthly' | 'one-off'>('monthly');
  const [expenseActive, setExpenseActive] = useState<boolean>(false);

  const [activeTab, setActiveTab] = useState<'talent_ops' | 'revenue_clients' | 'terms_cash'>('talent_ops');

  // Compute Active Changes Payload for the Engine
  const activeChanges = useMemo<ScenarioChangePayload[]>(() => {
    const list: ScenarioChangePayload[] = [];

    if (hireActive && hireCount > 0) {
      list.push({
        lever: 'hire',
        op: 'set',
        value: hireCount,
        start_date: '2026-11-01',
        params: {
          count: hireCount,
          monthly_cost: hireMonthlyCost.toFixed(2),
        },
        is_assumption: true,
      });
    }

    if (delayActive && delayDays > 0) {
      list.push({
        lever: 'payment_delay',
        op: 'set',
        value: delayDays,
        start_date: '2026-11-01',
        params: {
          client: delayClient,
          days: delayDays,
        },
        is_assumption: true,
      });
    }

    if (depositActive && depositPct > 0) {
      list.push({
        lever: 'deposit_pct',
        op: 'set',
        value: depositPct,
        start_date: '2026-11-01',
        params: { pct: depositPct },
        is_assumption: true,
      });
    }

    if (termsActive && paymentTermsDays !== 0) {
      list.push({
        lever: 'payment_terms_days',
        op: 'set',
        value: paymentTermsDays,
        start_date: '2026-11-01',
        params: { days: paymentTermsDays },
        is_assumption: true,
      });
    }

    if (lostClientActive && lostClientName) {
      list.push({
        lever: 'lost_client',
        op: 'set',
        value: lostClientName,
        start_date: '2026-11-01',
        params: { client: lostClientName },
        is_assumption: true,
      });
    }

    if (priceActive && priceChangePct !== 0) {
      list.push({
        lever: 'price_change_pct',
        op: 'set',
        value: priceChangePct,
        start_date: '2026-11-01',
        params: { pct: priceChangePct },
        is_assumption: true,
      });
    }

    if (revActive && revChangePct !== 0) {
      list.push({
        lever: 'revenue_change_pct',
        op: 'set',
        value: revChangePct,
        start_date: '2026-11-01',
        params: { pct: revChangePct },
        is_assumption: true,
      });
    }

    if (expenseActive && expenseAmt > 0) {
      list.push({
        lever: 'expense_change',
        op: 'set',
        value: expenseAmt,
        start_date: '2026-11-01',
        params: { cadence: expenseCadence },
        is_assumption: true,
      });
    }

    return list;
  }, [
    hireActive,
    hireCount,
    hireMonthlyCost,
    delayActive,
    delayDays,
    delayClient,
    depositActive,
    depositPct,
    termsActive,
    paymentTermsDays,
    lostClientActive,
    lostClientName,
    priceActive,
    priceChangePct,
    revActive,
    revChangePct,
    expenseActive,
    expenseAmt,
    expenseCadence,
  ]);

  // Quick Preset Handlers
  const applyPreset = (preset: 'golden' | 'cash_shield' | 'stress_test' | 'clear') => {
    if (preset === 'clear') {
      setHireActive(false);
      setDelayActive(false);
      setDepositActive(false);
      setTermsActive(false);
      setLostClientActive(false);
      setPriceActive(false);
      setRevActive(false);
      setExpenseActive(false);
      if (onResetBaseline) onResetBaseline();
      return;
    }

    if (preset === 'golden') {
      setHireActive(true);
      setHireCount(2);
      setHireMonthlyCost(7000);
      setDelayActive(true);
      setDelayClient('Apex Systems');
      setDelayDays(30);
      setDepositActive(false);
      setTermsActive(false);
      setLostClientActive(false);
      setPriceActive(false);
      setRevActive(false);
      setExpenseActive(false);
      setActiveTab('talent_ops');
    } else if (preset === 'cash_shield') {
      setHireActive(false);
      setDelayActive(false);
      setDepositActive(true);
      setDepositPct(25);
      setPriceActive(true);
      setPriceChangePct(10);
      setTermsActive(false);
      setLostClientActive(false);
      setRevActive(false);
      setExpenseActive(false);
      setActiveTab('terms_cash');
    } else if (preset === 'stress_test') {
      setHireActive(true);
      setHireCount(2);
      setLostClientActive(true);
      setLostClientName('Apex Systems');
      setTermsActive(true);
      setPaymentTermsDays(15);
      setDelayActive(false);
      setDepositActive(false);
      setPriceActive(false);
      setRevActive(false);
      setExpenseActive(false);
      setActiveTab('revenue_clients');
    }
  };

  const handleRun = () => {
    if (!onRunScenario) return;
    const name =
      activeChanges.length === 0
        ? 'Baseline Reality'
        : activeChanges.map((c) => c.lever).join(' + ');
    onRunScenario(activeChanges, name);
  };

  // Instant Calculated Outflow/Inflow Delta Summary
  const monthlyOutflowDelta = useMemo(() => {
    let delta = 0;
    if (hireActive) delta += hireCount * hireMonthlyCost;
    if (expenseActive) {
      delta += expenseCadence === 'monthly' ? expenseAmt : expenseAmt / 12;
    }
    return delta;
  }, [hireActive, hireCount, hireMonthlyCost, expenseActive, expenseAmt, expenseCadence]);

  return (
    <div className="glass-panel overflow-hidden font-[var(--font-ui)] transition-all">
      {/* Header with Title and Preset Pills */}
      <div
        className="p-5 border-b flex flex-wrap justify-between items-center gap-3 bg-white/40 dark:bg-black/15 backdrop-blur-md"
        style={{ borderColor: 'var(--divider)' }}
      >
        <div>
          <div className="flex items-center space-x-2">
            <span
              className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-[var(--radius-chip)] inline-flex items-center space-x-1.5 glass-pill shadow-xs"
              style={{
                backgroundColor: 'var(--tag-computed-bg)',
                color: 'var(--tag-computed)',
              }}
            >
              <span>⚡</span>
              <span>Sensitivity Studio</span>
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-[var(--radius-chip)] font-[var(--font-mono)] glass-pill"
              style={{
                backgroundColor:
                  activeChanges.length > 0
                    ? 'var(--status-warning-bg)'
                    : 'var(--status-unverified-bg)',
                color:
                  activeChanges.length > 0
                    ? 'var(--status-warning)'
                    : 'var(--status-unverified)',
              }}
            >
              {activeChanges.length} Lever{activeChanges.length === 1 ? '' : 's'} Active
            </span>
          </div>
          <h2 className="text-lg font-bold mt-1 tracking-tight text-gradient-hero">
            Interactive What-If Scenario Levers
          </h2>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Adjust parameters to project cash runway deltas against the immutable baseline.
          </p>
        </div>

        {/* Quick Presets */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <span className="font-medium text-[11px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
            Presets:
          </span>
          <button
            type="button"
            onClick={() => applyPreset('golden')}
            className="px-3 py-1 rounded-[var(--radius-chip)] border font-semibold transition-all duration-200 glass-pill hover:scale-102 active:scale-98 shadow-xs"
            style={{
              backgroundColor: 'var(--tag-inferred-bg)',
              color: 'var(--tag-inferred)',
              borderColor: 'var(--tag-inferred)',
            }}
          >
            ★ Golden Demo (2 Devs + 30d Delay)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('cash_shield')}
            className="px-3 py-1 rounded-[var(--radius-chip)] border font-semibold transition-all duration-200 glass-pill hover:scale-102 active:scale-98 shadow-xs"
            style={{
              backgroundColor: 'var(--status-verified-bg)',
              color: 'var(--status-verified)',
              borderColor: 'var(--status-verified)',
            }}
          >
            🛡 Cash Shield (+25% Deposit)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('stress_test')}
            className="px-3 py-1 rounded-[var(--radius-chip)] border font-semibold transition-all duration-200 glass-pill hover:scale-102 active:scale-98 shadow-xs"
            style={{
              backgroundColor: 'var(--status-failed-bg)',
              color: 'var(--status-failed)',
              borderColor: 'var(--status-failed)',
            }}
          >
            ⚠ Black Swan (Lost Apex)
          </button>
          {activeChanges.length > 0 && (
            <button
              type="button"
              onClick={() => applyPreset('clear')}
              className="px-2.5 py-1 rounded-[var(--radius-chip)] border font-medium transition-all duration-200 glass-pill hover:scale-102 active:scale-98"
              style={{
                backgroundColor: 'var(--surface)',
                borderColor: 'var(--ui-border)',
                color: 'var(--muted)',
              }}
            >
              Reset All
            </button>
          )}
        </div>
      </div>

      {/* Category Tabs */}
      <div
        className="flex border-b text-xs font-semibold px-4 pt-2 gap-4"
        style={{
          borderColor: 'var(--divider)',
          backgroundColor: 'var(--surface)',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('talent_ops')}
          className={`pb-2.5 px-2 border-b-2 transition ${
            activeTab === 'talent_ops'
              ? 'border-[var(--primary)] text-[var(--primary)] font-bold'
              : 'border-transparent text-[var(--muted)] hover:text-[var(--text)]'
          }`}
        >
          1. Headcount & Direct Outflows
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('revenue_clients')}
          className={`pb-2.5 px-2 border-b-2 transition ${
            activeTab === 'revenue_clients'
              ? 'border-[var(--primary)] text-[var(--primary)] font-bold'
              : 'border-transparent text-[var(--muted)] hover:text-[var(--text)]'
          }`}
        >
          2. Client Delays & Churn Risk
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('terms_cash')}
          className={`pb-2.5 px-2 border-b-2 transition ${
            activeTab === 'terms_cash'
              ? 'border-[var(--primary)] text-[var(--primary)] font-bold'
              : 'border-transparent text-[var(--muted)] hover:text-[var(--text)]'
          }`}
        >
          3. Payment Terms, Deposits & Pricing
        </button>
      </div>

      {/* Main Lever Configuration Body */}
      <div className="p-6">
        {/* Tab 1: Talent & Direct Outflows */}
        {activeTab === 'talent_ops' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Lever: Hire Developers */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                hireActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: hireActive ? 'var(--primary)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-hire-toggle"
                    checked={hireActive}
                    onChange={(e) => setHireActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--primary)]"
                  />
                  <label htmlFor="lever-hire-toggle" className="text-xs font-bold uppercase tracking-wider cursor-pointer" style={{ color: 'var(--text)' }}>
                    Lever: Hire Staff (`hire`)
                  </label>
                </div>
                {hireActive && (
                  <span
                    className="text-[11px] font-mono px-2 py-0.5 rounded-[var(--radius-chip)] font-bold"
                    style={{
                      backgroundColor: 'var(--status-warning-bg)',
                      color: 'var(--status-warning)',
                    }}
                  >
                    -${(hireCount * hireMonthlyCost).toLocaleString()}/mo
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {/* Stepper for Count */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: 'var(--muted)' }}>New Full-Time Roles:</span>
                    <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                      {hireCount} Staff
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      disabled={!hireActive || hireCount <= 0}
                      onClick={() => setHireCount((c) => Math.max(0, c - 1))}
                      className="px-3 py-1.5 rounded-[var(--radius-control)] border text-sm font-bold transition disabled:opacity-40"
                      style={{
                        backgroundColor: 'var(--surface)',
                        borderColor: 'var(--ui-border)',
                        color: 'var(--text)',
                      }}
                    >
                      -
                    </button>
                    <input
                      type="range"
                      min={0}
                      max={8}
                      disabled={!hireActive}
                      value={hireCount}
                      onChange={(e) => setHireCount(parseInt(e.target.value) || 0)}
                      className="w-full accent-[var(--primary)] cursor-pointer disabled:opacity-40"
                    />
                    <button
                      type="button"
                      disabled={!hireActive || hireCount >= 10}
                      onClick={() => setHireCount((c) => c + 1)}
                      className="px-3 py-1.5 rounded-[var(--radius-control)] border text-sm font-bold transition disabled:opacity-40"
                      style={{
                        backgroundColor: 'var(--surface)',
                        borderColor: 'var(--ui-border)',
                        color: 'var(--text)',
                      }}
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Monthly Cost per Head */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: 'var(--muted)' }}>Cost Per Head (Monthly):</span>
                    <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                      ${hireMonthlyCost.toLocaleString()} / mo
                    </span>
                  </div>
                  <input
                    type="range"
                    min={4000}
                    max={15000}
                    step={500}
                    disabled={!hireActive}
                    value={hireMonthlyCost}
                    onChange={(e) => setHireMonthlyCost(parseInt(e.target.value) || 0)}
                    className="w-full accent-[var(--primary)] cursor-pointer disabled:opacity-40"
                  />
                  <div className="flex justify-between text-[11px] font-mono mt-1" style={{ color: 'var(--muted)' }}>
                    <span>$4,000 (Junior)</span>
                    <span>$7,000 (Mid)</span>
                    <span>$15,000 (Lead)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Lever: Expense Change */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                expenseActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: expenseActive ? 'var(--primary)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-expense-toggle"
                    checked={expenseActive}
                    onChange={(e) => setExpenseActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--primary)]"
                  />
                  <label htmlFor="lever-expense-toggle" className="text-xs font-bold uppercase tracking-wider cursor-pointer" style={{ color: 'var(--text)' }}>
                    Lever: OpEx Delta (`expense_change`)
                  </label>
                </div>
                {expenseActive && (
                  <span
                    className="text-[11px] font-mono px-2 py-0.5 rounded-[var(--radius-chip)] font-bold"
                    style={{
                      backgroundColor: 'var(--tag-computed-bg)',
                      color: 'var(--tag-computed)',
                    }}
                  >
                    -${expenseAmt.toLocaleString()} ({expenseCadence})
                  </span>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: 'var(--muted)' }}>Expense Amount:</span>
                    <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                      ${expenseAmt.toLocaleString()}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={500}
                    max={25000}
                    step={500}
                    disabled={!expenseActive}
                    value={expenseAmt}
                    onChange={(e) => setExpenseAmt(parseInt(e.target.value) || 0)}
                    className="w-full accent-[var(--primary)] cursor-pointer disabled:opacity-40"
                  />
                </div>

                <div>
                  <span className="text-xs block mb-1" style={{ color: 'var(--muted)' }}>
                    Cadence:
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <button
                      type="button"
                      disabled={!expenseActive}
                      onClick={() => setExpenseCadence('monthly')}
                      className={`py-1.5 rounded-[var(--radius-control)] border font-semibold transition ${
                        expenseCadence === 'monthly'
                          ? 'border-[var(--primary)] bg-[var(--surface)] text-[var(--primary)] shadow-sm'
                          : 'border-[var(--divider)] opacity-60'
                      }`}
                    >
                      Monthly Recurring
                    </button>
                    <button
                      type="button"
                      disabled={!expenseActive}
                      onClick={() => setExpenseCadence('one-off')}
                      className={`py-1.5 rounded-[var(--radius-control)] border font-semibold transition ${
                        expenseCadence === 'one-off'
                          ? 'border-[var(--primary)] bg-[var(--surface)] text-[var(--primary)] shadow-sm'
                          : 'border-[var(--divider)] opacity-60'
                      }`}
                    >
                      One-off Capital Outlay
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Client Delays & Churn Risk */}
        {activeTab === 'revenue_clients' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Lever: Client Payment Delay */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                delayActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: delayActive ? 'var(--primary)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-delay-toggle"
                    checked={delayActive}
                    onChange={(e) => setDelayActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--primary)]"
                  />
                  <label htmlFor="lever-delay-toggle" className="text-xs font-bold uppercase tracking-wider cursor-pointer" style={{ color: 'var(--text)' }}>
                    Lever: Client Delay (`payment_delay`)
                  </label>
                </div>
                {delayActive && (
                  <span
                    className="text-[11px] font-mono px-2 py-0.5 rounded-[var(--radius-chip)] font-bold"
                    style={{
                      backgroundColor: 'var(--status-warning-bg)',
                      color: 'var(--status-warning)',
                    }}
                  >
                    +{delayDays} Days Late
                  </span>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs block mb-1" style={{ color: 'var(--muted)' }}>
                    Target Concentrated Client:
                  </label>
                  <select
                    disabled={!delayActive}
                    value={delayClient}
                    onChange={(e) => setDelayClient(e.target.value)}
                    className="w-full p-2 text-xs rounded-[var(--radius-control)] border font-medium transition disabled:opacity-40"
                    style={{
                      backgroundColor: 'var(--surface)',
                      borderColor: 'var(--ui-border)',
                      color: 'var(--text)',
                    }}
                  >
                    <option value="Apex Systems">Apex Systems (38% Revenue Concentration)</option>
                    <option value="Globex Media">Globex Media (22% Revenue)</option>
                    <option value="Initech Corp">Initech Corp (14% Revenue)</option>
                    <option value="Soylent Group">Soylent Group (10% Revenue)</option>
                  </select>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: 'var(--muted)' }}>Payment Delay Offset:</span>
                    <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                      +{delayDays} Days
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={90}
                    step={5}
                    disabled={!delayActive}
                    value={delayDays}
                    onChange={(e) => setDelayDays(parseInt(e.target.value) || 0)}
                    className="w-full accent-[var(--primary)] cursor-pointer disabled:opacity-40"
                  />
                  <div className="flex justify-between text-[11px] font-mono mt-1" style={{ color: 'var(--muted)' }}>
                    <span>On Time (0d)</span>
                    <span>Standard Net 30 (+30d)</span>
                    <span>Severe (+90d)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Lever: Lost Client */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                lostClientActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: lostClientActive ? 'var(--status-failed)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-lost-toggle"
                    checked={lostClientActive}
                    onChange={(e) => setLostClientActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--status-failed)]"
                  />
                  <label htmlFor="lever-lost-toggle" className="text-xs font-bold uppercase tracking-wider cursor-pointer" style={{ color: 'var(--text)' }}>
                    Lever: Client Churn (`lost_client`)
                  </label>
                </div>
                {lostClientActive && (
                  <span
                    className="text-[11px] font-mono px-2 py-0.5 rounded-[var(--radius-chip)] font-bold"
                    style={{
                      backgroundColor: 'var(--status-failed-bg)',
                      color: 'var(--status-failed)',
                    }}
                  >
                    Revenue Zeroed Post-Nov 1
                  </span>
                )}
              </div>

              <div className="space-y-4">
                <p className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
                  Simulates immediate loss of an ongoing account. Eliminates all scheduled recurring receivables starting Nov 1.
                </p>
                <div>
                  <label className="text-xs block mb-1" style={{ color: 'var(--muted)' }}>
                    Select Lost Client:
                  </label>
                  <select
                    disabled={!lostClientActive}
                    value={lostClientName}
                    onChange={(e) => setLostClientName(e.target.value)}
                    className="w-full p-2 text-xs rounded-[var(--radius-control)] border font-medium transition disabled:opacity-40"
                    style={{
                      backgroundColor: 'var(--surface)',
                      borderColor: 'var(--ui-border)',
                      color: 'var(--text)',
                    }}
                  >
                    <option value="Apex Systems">Apex Systems (Hero Stress-Test: -$38,000/mo)</option>
                    <option value="Globex Media">Globex Media (-$22,000/mo)</option>
                    <option value="Initech Corp">Initech Corp (-$14,000/mo)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Payment Terms, Deposits & Pricing */}
        {activeTab === 'terms_cash' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Lever: Deposit % Upfront */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                depositActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: depositActive ? 'var(--status-verified)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-deposit-toggle"
                    checked={depositActive}
                    onChange={(e) => setDepositActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--status-verified)]"
                  />
                  <label htmlFor="lever-deposit-toggle" className="text-xs font-bold uppercase cursor-pointer" style={{ color: 'var(--text)' }}>
                    Deposit % (`deposit_pct`)
                  </label>
                </div>
              </div>
              <p className="text-[11px] mb-3" style={{ color: 'var(--muted)' }}>
                Upfront cash collected on contract start.
              </p>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: 'var(--muted)' }}>Upfront Rate:</span>
                <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                  {depositPct}%
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={50}
                step={5}
                disabled={!depositActive}
                value={depositPct}
                onChange={(e) => setDepositPct(parseInt(e.target.value) || 0)}
                className="w-full accent-[var(--status-verified)] cursor-pointer disabled:opacity-40"
              />
            </div>

            {/* Lever: Shift Payment Terms */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                termsActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: termsActive ? 'var(--primary)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-terms-toggle"
                    checked={termsActive}
                    onChange={(e) => setTermsActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--primary)]"
                  />
                  <label htmlFor="lever-terms-toggle" className="text-xs font-bold uppercase cursor-pointer" style={{ color: 'var(--text)' }}>
                    Terms Shift (`payment_terms`)
                  </label>
                </div>
              </div>
              <p className="text-[11px] mb-3" style={{ color: 'var(--muted)' }}>
                Shift all customer net invoice terms.
              </p>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: 'var(--muted)' }}>Shift Days:</span>
                <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                  {paymentTermsDays >= 0 ? `+${paymentTermsDays}d` : `${paymentTermsDays}d`}
                </span>
              </div>
              <input
                type="range"
                min={-15}
                max={30}
                step={5}
                disabled={!termsActive}
                value={paymentTermsDays}
                onChange={(e) => setPaymentTermsDays(parseInt(e.target.value) || 0)}
                className="w-full accent-[var(--primary)] cursor-pointer disabled:opacity-40"
              />
            </div>

            {/* Lever: Price Adjustment */}
            <div
              className={`p-4 rounded-[var(--radius-control)] border transition-all ${
                priceActive ? 'ring-1' : 'opacity-85'
              }`}
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: priceActive ? 'var(--primary)' : 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-price-toggle"
                    checked={priceActive}
                    onChange={(e) => setPriceActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[var(--primary)]"
                  />
                  <label htmlFor="lever-price-toggle" className="text-xs font-bold uppercase cursor-pointer" style={{ color: 'var(--text)' }}>
                    Price Change (`price_change`)
                  </label>
                </div>
              </div>
              <p className="text-[11px] mb-3" style={{ color: 'var(--muted)' }}>
                Rate change across all active contracts.
              </p>
              <div className="flex justify-between text-xs mb-1">
                <span style={{ color: 'var(--muted)' }}>Price Adjustment:</span>
                <span className="font-bold font-mono" style={{ color: 'var(--text)' }}>
                  {priceChangePct >= 0 ? `+${priceChangePct}%` : `${priceChangePct}%`}
                </span>
              </div>
              <input
                type="range"
                min={-20}
                max={30}
                step={5}
                disabled={!priceActive}
                value={priceChangePct}
                onChange={(e) => setPriceChangePct(parseInt(e.target.value) || 0)}
                className="w-full accent-[var(--primary)] cursor-pointer disabled:opacity-40"
              />
            </div>
          </div>
        )}

        {/* Live Calculated Delta Preview Banner */}
        <div
          className="mt-6 p-4 rounded-[var(--radius-control)] border flex flex-wrap justify-between items-center gap-4 transition-all duration-200 glass-panel"
          style={{
            borderColor: 'var(--divider)',
          }}
        >
          <div className="flex items-center space-x-4">
            <div>
              <span className="text-[11px] uppercase tracking-wider block font-semibold" style={{ color: 'var(--muted)' }}>
                Est. Monthly Outflow Burden:
              </span>
              <span
                className="text-base font-bold font-[var(--font-mono)] tabular-nums"
                style={{
                  color: monthlyOutflowDelta > 0 ? 'var(--status-warning)' : 'var(--text)',
                }}
              >
                {monthlyOutflowDelta > 0 ? `+$${monthlyOutflowDelta.toLocaleString()}/mo` : '$0.00'}
              </span>
            </div>

            <div className="h-8 w-px" style={{ backgroundColor: 'var(--divider)' }} />

            <div>
              <span className="text-[11px] uppercase tracking-wider block font-semibold" style={{ color: 'var(--muted)' }}>
                Cash Timing Impact:
              </span>
              <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                {delayActive ? `${delayClient} delayed +${delayDays}d` : 'Standard scheduled inflows'}
              </span>
            </div>

            {depositActive && (
              <>
                <div className="h-8 w-px" style={{ backgroundColor: 'var(--divider)' }} />
                <div>
                  <span className="text-[11px] uppercase tracking-wider block font-semibold" style={{ color: 'var(--muted)' }}>
                    Working Capital Relief:
                  </span>
                  <span className="text-xs font-semibold" style={{ color: 'var(--status-verified)' }}>
                    +{depositPct}% collected upfront
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Action Trigger Buttons */}
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleRun}
              disabled={isLoading}
              className="px-6 py-2.5 rounded-[var(--radius-control)] text-xs font-bold shadow-md transition-all duration-200 hover:scale-102 active:scale-98 disabled:opacity-50 inline-flex items-center space-x-2"
              style={{
                background: 'var(--primary-gradient)',
                color: 'var(--on-primary)',
              }}
            >
              {isLoading ? (
                <>
                  <span className="animate-spin text-sm">⟳</span>
                  <span>Executing Engine Math...</span>
                </>
              ) : (
                <>
                  <span>⚡</span>
                  <span>Run Scenario Simulation ({activeChanges.length})</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScenarioLeverDock;
