/**
 * topoConfig.ts — 拓扑图布局常量配置
 * 包含节点尺寸、间距、连线样式、状态配色等全局常量
 */

/** 拓扑图布局常量配置 */
export const TOPO_LAYOUT_CONFIG = {
  /** 节点尺寸（宽 × 高），单位: px */
  nodeSize: {
    system: { width: 160, height: 52 },
    phase:  { width: 200, height: 60 },
    agent:  { width: 180, height: 52 },
    tool:   { width: 140, height: 40 },
  },

  /** 间距配置 */
  spacing: {
    /** 相邻层级之间的水平间距（父→子方向） */
    levelGap: 80,
    /** 同一父节点下相邻兄弟之间的垂直间距 */
    siblingGap: 16,
  },

  /** 画布内边距 */
  padding: {
    top: 30,
    right: 40,
    bottom: 30,
    left: 30,
  },

  /** 连线配置 */
  edge: {
    /** 贝塞尔曲线的水平控制点偏移比例 (0~1, 相对于源-目标水平距离) */
    bezierControlRatio: 0.5,
    /** 线宽 */
    strokeWidth: 1.5,
    /** active 状态连线颜色 */
    activeColor: '#3B82F6',
    /** completed 状态连线颜色 */
    completedColor: '#CBD5E1',
  },

  /** 节点圆角半径 */
  borderRadius: 12,
} as const;

/** 布局配置类型 */
export type TopoLayoutConfig = typeof TOPO_LAYOUT_CONFIG;
