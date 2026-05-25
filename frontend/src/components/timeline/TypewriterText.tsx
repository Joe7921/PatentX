/**
 * TypewriterText.tsx — 打字机效果组件
 * 使用 requestAnimationFrame 逐字渲染文本，带闪烁光标效果
 */
import React, { useEffect, useRef, useState } from 'react';

interface TypewriterTextProps {
  /** 要显示的完整文本 */
  text: string;
  /** 每个字符的显示间隔(毫秒)，默认30 */
  speed?: number;
  /** 文本完全显示后的回调 */
  onComplete?: () => void;
}

export default function TypewriterText({ text, speed = 30, onComplete }: TypewriterTextProps) {
  const [displayedLength, setDisplayedLength] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const rafRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    setDisplayedLength(0);
    setIsComplete(false);
    lastTimeRef.current = 0;

    let currentLen = 0;
    const totalLen = text.length;

    if (totalLen === 0) {
      setIsComplete(true);
      onComplete?.();
      return;
    }

    const animate = (timestamp: number) => {
      if (!mountedRef.current) return;

      if (lastTimeRef.current === 0) {
        lastTimeRef.current = timestamp;
      }

      const elapsed = timestamp - lastTimeRef.current;

      if (elapsed >= speed) {
        const charsToAdd = Math.floor(elapsed / speed);
        currentLen = Math.min(currentLen + charsToAdd, totalLen);
        setDisplayedLength(currentLen);
        lastTimeRef.current = timestamp;
      }

      if (currentLen < totalLen) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        setIsComplete(true);
        onComplete?.();
      }
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      mountedRef.current = false;
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      // 组件卸载时立即显示完整文字(通过父组件直接渲染text)
    };
  }, [text, speed, onComplete]);

  return (
    <span>
      {text.slice(0, displayedLength)}
      {/* 闪烁光标，完成后隐藏 */}
      {!isComplete && (
        <span className="inline-block w-[2px] h-[1em] bg-current ml-0.5 animate-pulse align-text-bottom" />
      )}
    </span>
  );
}
