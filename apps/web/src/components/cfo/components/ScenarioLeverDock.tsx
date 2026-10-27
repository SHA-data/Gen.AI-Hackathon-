import React, { useState, useMemo } from 'react';
import { Zap, ShieldCheck, AlertTriangle, Play, RefreshCw, Check, CheckCircle2 } from 'lucide-react';

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

    if (lostClientActive && lostClientName.trim()) {
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
        lever: 'price_change',
        op: 'set',
        value: priceChangePct,
        start_date: '2026-11-01',
        params: { pct: priceChangePct },
        is_assumption: true,
      });
    }

    if (revActive && revChangePct !== 0) {
      list.push({
        lever: 'revenue_change',
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
        params: {
          amount: expenseAmt,
          cadence: expenseCadence,
        },
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
    <div className="space-y-4 font-sans">
      {/* Header with Title and Preset Pills */}
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full clay-pill-sage inline-flex items-center space-x-1.5 shadow-xs">
              <Zap className="w-3.5 h-3.5" />
              <span>Sensitivity Studio</span>
            </span>
            <span className="text-xs font-bold px-3 py-1 rounded-full clay-card-inset text-slate-800 font-mono">
              {activeChanges.length} Lever{activeChanges.length === 1 ? '' : 's'} Active
            </span>
          </div>
          <h2 className="text-lg font-extrabold mt-1 text-slate-900 tracking-tight">
            Interactive What-If Scenario Levers
          </h2>
          <p className="text-xs text-slate-600 font-semibold">
            Adjust parameters to project cash runway deltas against the immutable baseline.
          </p>
        </div>

        {/* Quick Presets */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <span className="font-bold text-slate-500">Presets:</span>
          <button
            type="button"
            onClick={() => applyPreset('golden')}
            className="clay-btn px-3.5 py-1.5 rounded-full font-bold text-slate-800 flex items-center space-x-1"
          >
            <Check className="w-3.5 h-3.5 text-[#648283]" />
            <span>Golden Demo (2 Devs + 30d Delay)</span>
          </button>
          <button
            type="button"
            onClick={() => applyPreset('cash_shield')}
            className="clay-btn px-3.5 py-1.5 rounded-full font-bold text-slate-800 flex items-center space-x-1"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Cash Shield (+25% Deposit)</span>
          </button>
          <button
            type="button"
            onClick={() => applyPreset('stress_test')}
            className="clay-btn px-3.5 py-1.5 rounded-full font-bold text-slate-800 flex items-center space-x-1"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
            <span>Black Swan (Lost Apex)</span>
          </button>
          {activeChanges.length > 0 && (
            <button
              type="button"
              onClick={() => applyPreset('clear')}
              className="clay-btn px-3 py-1 rounded-full font-bold text-slate-600 hover:text-slate-900"
            >
              Reset All
            </button>
          )}
        </div>
      </div>

      {/* Category Tabs (Segmented Tab Bar from Image 2) */}
      <div className="clay-segmented-bar flex items-center space-x-1 text-xs font-bold">
        <button
          type="button"
          onClick={() => setActiveTab('talent_ops')}
          className={`px-4 py-2 rounded-full transition-all flex-1 text-center ${
            activeTab === 'talent_ops'
              ? 'clay-pill-sage text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          1. Headcount & Direct Outflows
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('revenue_clients')}
          className={`px-4 py-2 rounded-full transition-all flex-1 text-center ${
            activeTab === 'revenue_clients'
              ? 'clay-pill-teal text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          2. Client Delays & Churn Risk
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('terms_cash')}
          className={`px-4 py-2 rounded-full transition-all flex-1 text-center ${
            activeTab === 'terms_cash'
              ? 'clay-pill-lavender text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          3. Payment Terms, Deposits & Pricing
        </button>
      </div>

      {/* Main Lever Configuration Body */}
      <div className="pt-2">
        {/* Tab 1: Talent & Direct Outflows */}
        {activeTab === 'talent_ops' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Lever: Hire Developers */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${hireActive ? 'ring-2 ring-[#648283]' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-hire-toggle"
                    checked={hireActive}
                    onChange={(e) => setHireActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[#648283]"
                  />
                  <label htmlFor="lever-hire-toggle" className="text-xs font-extrabold uppercase tracking-wide text-slate-900 cursor-pointer">
                    Lever: Hire Staff (`hire`)
                  </label>
                </div>
                {hireActive && (
                  <span className="clay-card-inset text-[11px] font-mono font-black text-rose-700 px-3 py-1 rounded-full">
                    -${(hireCount * hireMonthlyCost).toLocaleString()}/mo
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {/* Stepper for Count */}
                <div>
                  <div className="flex justify-between text-xs mb-1.5 font-bold text-slate-700">
                    <span>New Full-Time Roles:</span>
                    <span className="font-mono text-slate-900 font-black">
                      {hireCount} Staff
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      disabled={!hireActive || hireCount <= 0}
                      onClick={() => setHireCount((c) => Math.max(0, c - 1))}
                      className="clay-btn w-8 h-8 rounded-full text-base font-bold flex items-center justify-center disabled:opacity-40"
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
                      className="w-full accent-[#648283] cursor-pointer disabled:opacity-40"
                    />
                    <button
                      type="button"
                      disabled={!hireActive || hireCount >= 10}
                      onClick={() => setHireCount((c) => c + 1)}
                      className="clay-btn w-8 h-8 rounded-full text-base font-bold flex items-center justify-center disabled:opacity-40"
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Monthly Cost per Head */}
                <div>
                  <div className="flex justify-between text-xs mb-1 font-bold text-slate-700">
                    <span>Cost Per Head (Monthly):</span>
                    <span className="font-mono text-slate-900 font-black">
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
                    className="w-full accent-[#648283] cursor-pointer disabled:opacity-40"
                  />
                  <div className="flex justify-between text-[10px] font-mono text-slate-500 font-bold mt-1">
                    <span>$4,000 (Junior)</span>
                    <span>$7,000 (Mid)</span>
                    <span>$15,000 (Lead)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Lever: Expense Change */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${expenseActive ? 'ring-2 ring-[#648283]' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-expense-toggle"
                    checked={expenseActive}
                    onChange={(e) => setExpenseActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[#648283]"
                  />
                  <label htmlFor="lever-expense-toggle" className="text-xs font-extrabold uppercase tracking-wide text-slate-900 cursor-pointer">
                    Lever: Opex Delta (`expense_change`)
                  </label>
                </div>
                {expenseActive && (
                  <span className="clay-card-inset text-[11px] font-mono font-black text-rose-700 px-3 py-1 rounded-full">
                    -${expenseAmt.toLocaleString()}
                  </span>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1.5 font-bold text-slate-700">
                    <span>Expense Amount:</span>
                    <span className="font-mono text-slate-900 font-black">
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
                    className="w-full accent-[#648283] cursor-pointer disabled:opacity-40"
                  />
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <button
                    type="button"
                    disabled={!expenseActive}
                    onClick={() => setExpenseCadence('monthly')}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold transition flex-1 text-center ${
                      expenseCadence === 'monthly'
                        ? 'clay-pill-sage text-slate-900'
                        : 'clay-btn text-slate-600'
                    }`}
                  >
                    Monthly Recurring
                  </button>
                  <button
                    type="button"
                    disabled={!expenseActive}
                    onClick={() => setExpenseCadence('one-off')}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold transition flex-1 text-center ${
                      expenseCadence === 'one-off'
                        ? 'clay-pill-sage text-slate-900'
                        : 'clay-btn text-slate-600'
                    }`}
                  >
                    One-off Capital Outlay
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Revenue & Clients */}
        {activeTab === 'revenue_clients' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Lever: Client Payment Delay */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${delayActive ? 'ring-2 ring-amber-500' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-delay-toggle"
                    checked={delayActive}
                    onChange={(e) => setDelayActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-amber-600"
                  />
                  <label htmlFor="lever-delay-toggle" className="text-xs font-extrabold uppercase tracking-wide text-slate-900 cursor-pointer">
                    Client Delay (`payment_delay`)
                  </label>
                </div>
                {delayActive && (
                  <span className="clay-card-inset text-[11px] font-mono font-black text-amber-800 px-3 py-1 rounded-full">
                    +{delayDays}d Delay
                  </span>
                )}
              </div>
              <div className="space-y-3">
                <input
                  type="text"
                  value={delayClient}
                  onChange={(e) => setDelayClient(e.target.value)}
                  className="w-full clay-card-inset px-3 py-2 rounded-xl text-xs text-slate-900 font-bold"
                  placeholder="Target Client Name"
                />
                <input
                  type="range"
                  min={10}
                  max={90}
                  step={5}
                  disabled={!delayActive}
                  value={delayDays}
                  onChange={(e) => setDelayDays(parseInt(e.target.value) || 0)}
                  className="w-full accent-amber-600 cursor-pointer disabled:opacity-40"
                />
              </div>
            </div>

            {/* Lever: Lost Client (Churn) */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${lostClientActive ? 'ring-2 ring-rose-500' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-lost-toggle"
                    checked={lostClientActive}
                    onChange={(e) => setLostClientActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-rose-600"
                  />
                  <label htmlFor="lever-lost-toggle" className="text-xs font-extrabold uppercase tracking-wide text-slate-900 cursor-pointer">
                    Lost Client (`lost_client`)
                  </label>
                </div>
              </div>
              <div className="space-y-3">
                <input
                  type="text"
                  value={lostClientName}
                  onChange={(e) => setLostClientName(e.target.value)}
                  className="w-full clay-card-inset px-3 py-2 rounded-xl text-xs text-slate-900 font-bold"
                  placeholder="Client Name (e.g. Apex Systems)"
                />
                <p className="text-[11px] text-slate-600 font-medium">
                  Immediately zeros out all projected future inflows from this client.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Terms & Cash */}
        {activeTab === 'terms_cash' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Lever: Upfront Deposit % */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${depositActive ? 'ring-2 ring-emerald-500' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-deposit-toggle"
                    checked={depositActive}
                    onChange={(e) => setDepositActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-emerald-600"
                  />
                  <label htmlFor="lever-deposit-toggle" className="text-xs font-extrabold uppercase text-slate-900 cursor-pointer">
                    Deposit % (`deposit_pct`)
                  </label>
                </div>
              </div>
              <div className="flex justify-between text-xs font-bold text-slate-700">
                <span>Deposit Rate:</span>
                <span className="font-mono text-slate-900 font-black">{depositPct}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={50}
                step={5}
                disabled={!depositActive}
                value={depositPct}
                onChange={(e) => setDepositPct(parseInt(e.target.value) || 0)}
                className="w-full accent-emerald-600 cursor-pointer disabled:opacity-40"
              />
            </div>

            {/* Lever: Shift Payment Terms */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${termsActive ? 'ring-2 ring-[#648283]' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-terms-toggle"
                    checked={termsActive}
                    onChange={(e) => setTermsActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-[#648283]"
                  />
                  <label htmlFor="lever-terms-toggle" className="text-xs font-extrabold uppercase text-slate-900 cursor-pointer">
                    Terms (`payment_terms`)
                  </label>
                </div>
              </div>
              <div className="flex justify-between text-xs font-bold text-slate-700">
                <span>Shift Days:</span>
                <span className="font-mono text-slate-900 font-black">
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
                className="w-full accent-[#648283] cursor-pointer disabled:opacity-40"
              />
            </div>

            {/* Lever: Price Adjustment */}
            <div className={`clay-cushion p-5 rounded-3xl space-y-3 ${priceActive ? 'ring-2 ring-purple-500' : 'opacity-80'}`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="lever-price-toggle"
                    checked={priceActive}
                    onChange={(e) => setPriceActive(e.target.checked)}
                    className="w-4 h-4 rounded cursor-pointer accent-purple-600"
                  />
                  <label htmlFor="lever-price-toggle" className="text-xs font-extrabold uppercase text-slate-900 cursor-pointer">
                    Price (`price_change`)
                  </label>
                </div>
              </div>
              <div className="flex justify-between text-xs font-bold text-slate-700">
                <span>Price Adjustment:</span>
                <span className="font-mono text-slate-900 font-black">
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
                className="w-full accent-purple-600 cursor-pointer disabled:opacity-40"
              />
            </div>
          </div>
        )}

        {/* Live Calculated Delta Preview Banner */}
        <div className="mt-5 p-4 clay-card-inset rounded-2xl flex flex-wrap justify-between items-center gap-4">
          <div className="flex items-center space-x-5 text-xs">
            <div>
              <span className="text-[10px] uppercase tracking-wider block font-bold text-slate-500">
                Est. Monthly Outflow Burden:
              </span>
              <span className={`text-base font-extrabold font-mono ${monthlyOutflowDelta > 0 ? 'text-rose-700' : 'text-slate-900'}`}>
                {monthlyOutflowDelta > 0 ? `+$${monthlyOutflowDelta.toLocaleString()}/mo` : '$0.00'}
              </span>
            </div>

            <div className="h-8 w-px bg-slate-300" />

            <div>
              <span className="text-[10px] uppercase tracking-wider block font-bold text-slate-500">
                Cash Timing Impact:
              </span>
              <span className="text-xs font-bold text-slate-800">
                {delayActive ? `${delayClient} delayed +${delayDays}d` : 'Standard scheduled inflows'}
              </span>
            </div>

            {depositActive && (
              <>
                <div className="h-8 w-px bg-slate-300" />
                <div>
                  <span className="text-[10px] uppercase tracking-wider block font-bold text-slate-500">
                    Working Capital Relief:
                  </span>
                  <span className="text-xs font-black text-emerald-700">
                    +{depositPct}% collected upfront
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Action Trigger Buttons */}
          <button
            type="button"
            onClick={handleRun}
            disabled={isLoading}
            className="px-6 py-2.5 clay-pill-sage rounded-full text-xs font-black text-slate-900 flex items-center space-x-2 shadow-md transition-all hover:scale-102"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Executing Engine Math...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Scenario Simulation ({activeChanges.length})</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScenarioLeverDock;
