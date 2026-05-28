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

export default function AuroraBackground({ isHovered = false }: { isHovered?: boolean }) {
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

    // 使用极其干净、清透的马卡龙/柔和色系，Alpha 值调低以防正片叠底变脏
    const baseColors = [
      { r: 80, g: 160, b: 255, a: 0.35 },  // 清透天蓝
      { r: 200, g: 120, b: 255, a: 0.25 },  // 清透粉紫
      { r: 80, g: 220, b: 240, a: 0.35 },  // 清透青蓝
    ];
    // 复制两组，总共 6 个极光球，均匀铺满整个输入舱背部
    const colors = [...baseColors, ...baseColors];

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
      ctx.globalCompositeOperation = 'multiply';

      const time = (Date.now() - startTime) * 0.0008;
      const hovered = isHoveredRef.current;

      particles.forEach((p, index) => {
        // 让 6 个球均匀分布在容器宽度的 10% 到 90% 之间，形成一条完整的光晕带
        const percent = particles.length > 1 ? index / (particles.length - 1) : 0.5;
        const homeX = width * 0.1 + (width * 0.8 * percent);
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

        // 半径适中，6 个球叠加足以填满空隙
        const targetRadius = hovered ? 160 : 120;
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
        filter: 'blur(32px)' // 提高一点模糊度，让球与球之间融合得更完美
      }}
    />
  );
}
