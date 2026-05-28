import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  tx: number;
  ty: number;
  radius: number;
  r: number;
  g: number;
  b: number;
  a: number;
  stiffness: number;
  damping: number;
}

interface AuroraBackgroundProps {
  isHovered?: boolean;
}

export default function AuroraBackground({ isHovered = false }: AuroraBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isHoveredRef = useRef(isHovered);

  useEffect(() => {
    isHoveredRef.current = isHovered;
  }, [isHovered]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let animationFrameId: number;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      width = parent.clientWidth;
      height = parent.clientHeight;
      canvas.width = width;
      canvas.height = height;
    };

    // 浣跨敤鏋佸叾骞插噣銆佹竻閫忕殑椹崱榫?鏌斿拰鑹茬郴锛孉lpha 鍊艰皟浣庝互闃叉鐗囧彔搴曞彉鑴?    const baseColors = [
      { r: 80, g: 160, b: 255, a: 0.35 },  // 娓呴€忓ぉ钃?      { r: 200, g: 120, b: 255, a: 0.25 },  // 娓呴€忕矇绱?      { r: 80, g: 220, b: 240, a: 0.35 },  // 娓呴€忛潚钃?    ];
    // 澶嶅埗 5 缁勶紝鎬诲叡 15 涓瀬鍏夌悆锛屽潎鍖€閾烘弧鏁翠釜杈撳叆鑸辫儗閮?    const colors = [...baseColors, ...baseColors, ...baseColors, ...baseColors, ...baseColors];

    const particles: Particle[] = colors.map((c, i) => {
      return {
        x: width / 2,
        y: height / 2,
        vx: 0,
        vy: 0,
        tx: width / 2,
        ty: height / 2,
        radius: 0, 
        r: c.r, g: c.g, b: c.b, a: c.a,
        stiffness: 0.0015 + Math.random() * 0.001,
        damping: 0.85 + Math.random() * 0.04,
      };
    });

    window.addEventListener('resize', resize);
    resize();

    const startTime = Date.now();

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = 'screen';

      const time = (Date.now() - startTime) * 0.0008;
      const hovered = isHoveredRef.current;

      particles.forEach((p, index) => {
        // 璁?15 涓悆鍧囧寑鍒嗗竷鍦ㄥ鍣ㄥ搴︾殑 -10% 鍒?110% 涔嬮棿锛屽舰鎴愪竴鏉″畬鏁寸殑鍏夋檿甯?        const percent = particles.length > 1 ? index / (particles.length - 1) : 0.5;
        const homeX = -width * 0.1 + (width * 1.2 * percent);
        const homeY = height / 2;

        const spreadX = hovered ? width * 0.2 : width * 0.1;
        const spreadY = hovered ? height * 0.3 : height * 0.15;
        
        const floatX = Math.sin(time * 0.8 + index * 2.5) * spreadX;
        const floatY = Math.cos(time * 0.6 + index * 1.5) * spreadY;
        
        const targetX = homeX + floatX;
        const targetY = homeY + floatY;

        p.tx += (targetX - p.tx) * 0.1;
        p.ty += (targetY - p.ty) * 0.1;

        const ax = (p.tx - p.x) * p.stiffness;
        const ay = (p.ty - p.y) * p.stiffness;

        p.vx = (p.vx + ax) * p.damping;
        p.vy = (p.vy + ay) * p.damping;

        p.x += p.vx;
        p.y += p.vy;

        // 鍝嶅簲寮忓崐寰勶紝鎮仠鏃舵寜姣斾緥鏀惧ぇ
        const baseRadius = Math.max(150, width / 10);
        const targetRadius = hovered ? baseRadius * 1.3 : baseRadius;
        p.radius += (targetRadius - p.radius) * 0.1;

        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
        grad.addColorStop(0, `rgba(${p.r}, ${p.g}, ${p.b}, ${p.a})`);
        grad.addColorStop(0.4, `rgba(${p.r}, ${p.g}, ${p.b}, ${p.a * 0.5})`);
        grad.addColorStop(1, `rgba(${p.r}, ${p.g}, ${p.b}, 0)`);
        
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <motion.canvas
      ref={canvasRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.5 }}
      className="absolute inset-0 pointer-events-none z-[-1] bg-transparent"
      style={{ 
        mixBlendMode: 'multiply', 
        filter: 'blur(32px)' // 鎻愰珮涓€鐐规ā绯婂害锛岃鐞冧笌鐞冧箣闂磋瀺鍚堝緱鏇村畬缇?      }}
    />
  );
};
