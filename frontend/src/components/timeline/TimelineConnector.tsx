/**
 * TimelineConnector.tsx — 时间线连接器组件
 * 垂直线连接相邻的阶段节点，根据状态显示不同样式
 */
import React from 'react';

interface TimelineConnectorProps {
  /** 连接器状态 */
  status: 'completed' | 'active' | 'pending';
}

export default function TimelineConnector({ status }: TimelineConnectorProps) {
  // 根据状态确定连接器样式
  const getConnectorStyle = () => {
    switch (status) {
      case 'completed':
        return {
          lineClass: 'bg-gradient-to-b from-blue-400 to-blue-500',
          dotStyle: 'bg-blue-400',
          animated: true,
        };
      case 'active':
        return {
          lineClass: 'bg-gradient-to-b from-blue-400 to-slate-300',
          dotStyle: 'bg-blue-300',
          animated: false,
        };
      case 'pending':
      default:
        return {
          lineClass: 'border-l-2 border-dashed border-slate-300 bg-transparent',
          dotStyle: 'bg-slate-300',
          animated: false,
        };
    }
  };

  const style = getConnectorStyle();

  return (
    <div className="flex justify-center py-1">
      <div className="relative h-8 w-0.5 flex items-center justify-center">
        {status === 'pending' ? (
          /* 待定状态：虚线 */
          <div className="h-full border-l-2 border-dashed border-slate-300" />
        ) : (
          /* 已完成/进行中：实线带可选流动动画 */
          <div className={`h-full w-0.5 rounded-full ${style.lineClass} relative overflow-hidden`}>
            {style.animated && (
              <div
                className="absolute inset-0 w-full"
                style={{
                  background: 'linear-gradient(to bottom, transparent, rgba(255,255,255,0.6), transparent)',
                  animation: 'connectorFlow 1.5s ease-in-out infinite',
                }}
              />
            )}
          </div>
        )}
      </div>

      {/* 注入流动动画关键帧 */}
      {style.animated && (
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes connectorFlow {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
          }
        `}} />
      )}
    </div>
  );
}
