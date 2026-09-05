import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glow' | 'accent' | 'warning' | 'danger';
  interactive?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  variant = 'default',
  interactive = false,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-slate-900/60 border-slate-800/80 shadow-lg shadow-black/40',
    glow: 'bg-slate-900/70 border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.15)]',
    accent: 'bg-slate-900/70 border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.15)]',
    warning: 'bg-amber-950/20 border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.12)]',
    danger: 'bg-rose-950/20 border-rose-500/30 shadow-[0_0_20px_rgba(244,63,94,0.12)]',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'backdrop-blur-md rounded-xl border p-5 transition-all duration-300',
          variantStyles[variant],
          interactive && 'hover:border-cyan-400/50 hover:bg-slate-900/80 hover:translate-y-[-2px] cursor-pointer',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};
