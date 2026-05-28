/**
 * topoTypes.ts — 拓扑图布局专用类型定义
 * 包含布局结果、节点定位、连线路径等类型
 */

/** 布局结果：每个节点的定位信息 */
export interface NodeLayout {
  /** 原始拓扑节点 ID */
  nodeId: string;
  /** 节点左上角 X 坐标（像素） */
  x: number;
  /** 节点左上角 Y 坐标（像素） */
  y: number;
  /** 节点宽度（像素） */
  width: number;
  /** 节点高度（像素） */
  height: number;
}

/** 连线路径 */
export interface EdgePath {
  /** 连线唯一 ID */
  edgeId: string;
  /** 源节点 ID */
  sourceId: string;
  /** 目标节点 ID */
  targetId: string;
  /** SVG path d 属性值（贝塞尔曲线字符串） */
  path: string;
  /** 连线状态 */
  status: 'active' | 'completed';
}

/** 布局计算完整结果 */
export interface LayoutResult {
  /** 所有节点的定位信息 */
  nodes: NodeLayout[];
  /** 所有连线的路径信息 */
  edges: EdgePath[];
  /** 画布总宽度（包含 padding），单位 px */
  canvasWidth: number;
  /** 画布总高度（包含 padding），单位 px */
  canvasHeight: number;
}
