import { type LucideIcon, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { cn } from '@/lib/cn';

export interface StatCardProps {
  label: string;
  value: string;
  changePercent: number;
  changeSuffix?: string; // e.g. "vs. Vorwoche"
  icon: LucideIcon;
  tone: 'primary' | 'success' | 'warning' | 'info';
  /** When true, a negative change is treated as good (e.g. churn, deadlines). */
  invertTrend?: boolean;
  /** Optional second line below the main value (e.g. "23/27"). */
  subValue?: string;
}

const TONE: Record<StatCardProps['tone'], { fill: string; text: string }> = {
  primary: { fill: 'bg-primary-soft', text: 'text-primary' },
  success: { fill: 'bg-success-soft', text: 'text-success' },
  warning: { fill: 'bg-warning-soft', text: 'text-warning' },
  info:    { fill: 'bg-info-soft',    text: 'text-info' },
};

export function StatCard({
  label,
  value,
  changePercent,
  changeSuffix,
  icon: Icon,
  tone,
  invertTrend = false,
  subValue,
}: StatCardProps) {
  const cls = TONE[tone];
  const isZero = changePercent === 0;
  const isPositive = changePercent > 0;
  const isGood = invertTrend ? !isPositive : isPositive;
  const color = isZero ? 'text-ink-subtle' : isGood ? 'text-success' : 'text-warning';
  const TrendIcon = isZero ? Minus : isPositive ? ArrowUpRight : ArrowDownRight;

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="label-xs">{label}</p>
          <p className="nums mt-3 text-[32px] font-bold leading-none text-ink">
            {value}
            {subValue && <span className="text-ink-subtle">{subValue}</span>}
          </p>
        </div>
        <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg', cls.fill, cls.text)}>
          <Icon size={16} aria-hidden="true" />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-1.5 text-xs">
        <span className={cn('inline-flex items-center gap-0.5 font-semibold', color)}>
          <TrendIcon size={12} strokeWidth={2.5} aria-hidden="true" />
          {isZero ? '0,0 %' : `${isPositive ? '+' : ''}${changePercent.toFixed(1).replace('.', ',')} %`}
        </span>
        {changeSuffix && <span className="text-ink-muted">{changeSuffix}</span>}
      </div>
    </div>
  );
}
