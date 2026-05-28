import React, { useState } from 'react';
import { motion } from 'framer-motion';
import TypewriterSlogan from './TypewriterSlogan';
import UploadHub from './UploadHub';
import AuroraBackground from './AuroraBackground';

interface LandingPageProps {
  onUpload: (claimText: string) => void;
  disabled?: boolean;
}

export default function LandingPage({ onUpload, disabled }: LandingPageProps) {
  const [sloganReady, setSloganReady] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-center pt-24 pb-12 px-6 z-10">
      {/* SpaceX Style Logo */}
      <div className="absolute top-12 left-1/2 -translate-x-1/2 z-50">
        <motion.div 
          className="whitespace-nowrap font-google-sans text-[#1F1F1F] select-none"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: sloganReady ? 1 : 0, y: sloganReady ? 0 : -20 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <span className="text-[40px] font-semibold tracking-tight">Patent</span>
          <span className="text-[52px] font-extrabold tracking-tighter">X</span>
        </motion.div>
      </div>

      {/* Main Content Group: Slogan + Input Hub closely together */}
      <div className="flex flex-col items-center justify-center w-full max-w-4xl gap-16 mt-12">
        <div className="pointer-events-none relative w-full flex justify-center">
          <TypewriterSlogan 
            text="Tech Is All You Need" 
            onComplete={() => setSloganReady(true)} 
          />
        </div>

        {/* Upload Hub */}
        <motion.div
          className="w-full max-w-2xl relative z-20"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: sloganReady ? 1 : 0, y: sloganReady ? 0 : 20 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {/* 鏋佽嚧鏀舵潫锛氬厜鏅曞簳搴х揣璐磋緭鍏ヨ埍杈圭紭 */}
          {sloganReady && (
            <div className="absolute inset-[-40px] z-[-1] pointer-events-none">
              <AuroraBackground isHovered={isHovered} />
            </div>
          )}
          <UploadHub onUpload={onUpload} disabled={disabled} />
        </motion.div>
      </div>
    </div>
  );
}
