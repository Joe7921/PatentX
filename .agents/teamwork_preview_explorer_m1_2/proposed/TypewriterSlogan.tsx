import React from 'react';
import { motion } from 'framer-motion';

interface TypewriterSloganProps {
  text: string;
  onComplete: () => void;
}

export default function TypewriterSlogan({ text, onComplete }: TypewriterSloganProps) {
  // Split text into characters
  const characters = Array.from(text);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.06, // 打字机单字出现间隔
        delayChildren: 0.3,    // 开屏稍作停顿
      },
    },
  };

  const childVariants = {
    hidden: { opacity: 0, y: 10, filter: 'blur(8px)' },
    visible: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: {
        duration: 0.8,
        ease: [0.2, 0.65, 0.3, 0.9],
      },
    },
  };

  return (
    <motion.div
      className="text-center font-google-sans font-bold text-[#1F1F1F] tracking-tight leading-tight"
      style={{ fontSize: `min(8vw, 80px)` }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      onAnimationComplete={onComplete}
    >
      {characters.map((char, index) => (
        <motion.span key={index} variants={childVariants} className="inline-block whitespace-pre">
          {char}
        </motion.span>
      ))}
    </motion.div>
  );
}
