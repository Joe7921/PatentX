import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  tx: number;
  ty: number;
  radius: number;
  color: string;
  stiffness: number;
  damping: number;
}

export const AuroraBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = window.innerWidth;
    let height = window.innerHeight;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;

      // 调整粒子目标位置，防止越界
      particles.forEach(p => {
        p.tx = Math.random() * width;
        p.ty = Math.random() * height;
        p.radius = Math.min(width, height) * (0.4 + Math.random() * 0.2);
      });
    };

    // 科技蓝 (Sky/Blue)、梦幻紫 (Purple/Violet)、学术青 (Teal/Cyan)
    const colors = [
      'rgba(59, 130, 246, 0.35)',  // 科技蓝
      'rgba(147, 51, 234, 0.3)',   // 梦幻紫
      'rgba(6, 182, 212, 0.35)',   // 学术青
    ];

    const particles: Particle[] = colors.map(color => {
      const rx = Math.random() * width;
      const ry = Math.random() * height;
      return {
        x: rx,
        y: ry,
        vx: 0,
        vy: 0,
        tx: Math.random() * width,
        ty: Math.random() * height,
        radius: Math.min(width, height) * 0.5,
        color,
        stiffness: 0.0005 + Math.random() * 0.0008, // 极低的 stiffness 以确保漫反射平缓
        damping: 0.96 + Math.random() * 0.02,        // 阻尼
      };
    });

    window.addEventListener('resize', resize);
    resize();

    const draw = () => {
      // 使用 clearRect，保证透明背景
      ctx.clearRect(0, 0, width, height);

      // 采用正片叠底模式，使漫反射极光在浅色底上优雅晕染
      ctx.globalCompositeOperation = 'multiply';

      particles.forEach(p => {
        // 更新位置 (基于弹簧阻尼物理模型)
        const dist = Math.hypot(p.tx - p.x, p.ty - p.y);
        if (dist < 100) {
          p.tx = Math.random() * width;
          p.ty = Math.random() * height;
        }

        const ax = (p.tx - p.x) * p.stiffness;
        const ay = (p.ty - p.y) * p.stiffness;

        p.vx = (p.vx + ax) * p.damping;
        p.vy = (p.vy + ay) * p.damping;

        p.x += p.vx;
        p.y += p.vy;

        // 绘制漫反射径向渐变
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
        grad.addColorStop(0, p.color);
        grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
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
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-[-1] bg-slate-50"
      style={{ mixBlendMode: 'multiply' }}
    />
  );
};
