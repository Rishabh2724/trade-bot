"use client";

import Panel from "@/components/ui/Panel";
import { useAnalysis } from "@/lib/hooks";
import { useSymbolParams } from "@/lib/params";
import { findTimeframe } from "@/lib/symbols";
import { clockOf } from "@/lib/time";

import ActionCard from "./ActionCard";
import AlertsFeed from "./AlertsFeed";
import AskCopilot from "./AskCopilot";
import BiasCard from "./BiasCard";
import DataPanel from "./DataPanel";
import MarketFeed from "./MarketFeed";
import PatternsCard from "./PatternsCard";
import TradingViewChart from "./TradingViewChart";
import ZonesCard from "./ZonesCard";

export default function Dashboard() {
  const { symbol, timeframe, set } = useSymbolParams();
  const analysis = useAnalysis(symbol, timeframe);

  const { data, loading, error, stale } = analysis;
  const tv = findTimeframe(timeframe).tv;

  return (
    <div
      className={
        // Three columns on desktop: insights | chart + feed | data + alerts.
        // Stacks to one column below lg, where the whole page scrolls instead.
        "grid h-full min-h-0 grid-cols-1 gap-2 overflow-y-auto p-2 " +
        "lg:grid-cols-[19rem_minmax(0,1fr)_19rem] lg:grid-rows-[minmax(0,1fr)_15rem] lg:overflow-hidden"
      }
    >
      <Panel
        title="TradeCopilot AI insights"
        meta={data ? `${symbol} ${timeframe}` : undefined}
        loading={loading}
        error={error}
        stale={stale}
        className="lg:row-span-2"
      >
        {data ? (
          <div className="flex flex-col gap-3">
            <BiasCard data={data} />
            <PatternsCard data={data} />
            <ZonesCard data={data} />
            <ActionCard data={data} />
            <AskCopilot symbol={symbol} />
          </div>
        ) : null}
      </Panel>

      {/*
        The chart is a TradingView embed and does not depend on our backend, so
        it keeps rendering even when every analysis panel is erroring. It gets
        the refresh control because that is where the last-updated time is
        most useful.
      */}
      <Panel
        title={`${symbol} · ${timeframe}`}
        meta={
          <span className="flex items-center gap-2">
            {analysis.lastUpdated ? (
              <span>analysis {clockOf(analysis.lastUpdated)}</span>
            ) : null}
            <button
              type="button"
              onClick={analysis.refresh}
              className="rounded border border-line px-1.5 py-0.5 text-[10px] text-muted transition-colors hover:border-accent hover:text-accent"
            >
              Refresh
            </button>
          </span>
        }
        // The chart is the one panel whose content has no height of its own —
        // the embed fills its container. Below lg the panel body no longer
        // stretches, so give it a concrete height there.
        bodyClassName="p-0 h-80 lg:h-auto"
        className="min-h-[22rem] lg:min-h-0"
      >
        <TradingViewChart symbol={symbol} tvInterval={tv} />
      </Panel>

      <DataPanel
        data={data}
        loading={loading}
        error={error}
        stale={stale}
        className="min-h-[16rem] lg:min-h-0"
      />

      {/* Clicking a row switches the whole dashboard to that pair. */}
      <MarketFeed
        onSelect={(pair) => set("symbol", pair)}
        className="min-h-[12rem] lg:min-h-0"
      />

      <AlertsFeed
        data={data}
        loading={loading}
        error={error}
        stale={stale}
        className="min-h-[12rem] lg:min-h-0"
      />
    </div>
  );
}
