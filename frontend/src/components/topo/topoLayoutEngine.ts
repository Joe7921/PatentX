/**
 * topoLayoutEngine.ts — 水平树状布局算法
 * 基于 Reingold-Tilford 水平变体，纯 TypeScript 实现，零 React 依赖
 *
 * 算法流程：构建树 → 计算子树高度 → 分配坐标 → 生成连线
 * 方向：根在最左，子在右，兄弟垂直居中排列
 */

import type { TopologyNode, TopologyEdge } from '../../store/agenticTypes';
import { TOPO_LAYOUT_CONFIG, type TopoLayoutConfig } from './topoConfig';
import type { NodeLayout, EdgePath, LayoutResult } from './topoTypes';

// ============================================================
// 内部数据结构（不导出）
// ============================================================

/** 布局计算所需的内部树节点 */
interface LayoutTreeNode {
  /** 原始拓扑节点引用 */
  node: TopologyNode;
  /** 子节点列表 */
  children: LayoutTreeNode[];
  /** 层级深度（根 = 0） */
  depth: number;
  /** 布局计算后的 X 坐标（节点左上角） */
  x: number;
  /** 布局计算后的 Y 坐标（节点左上角） */
  y: number;
  /** 基于类型的节点宽度 */
  width: number;
  /** 基于类型的节点高度 */
  height: number;
  /** 以此节点为根的子树总高度占用（含所有后代 + 间距） */
  subtreeHeight: number;
}

// ============================================================
// 步骤 1：从扁平数组构建树
// ============================================================

/**
 * 将扁平的 TopologyNode[] 转换为树结构
 * 通过 parentId 字段建立父子关系
 * 时间复杂度 O(n)，空间复杂度 O(n)
 */
function buildTree(
  nodes: TopologyNode[],
  config: TopoLayoutConfig
): LayoutTreeNode | null {
  if (nodes.length === 0) return null;

  // 构建 id → LayoutTreeNode 映射
  const nodeMap = new Map<string, LayoutTreeNode>();

  for (const node of nodes) {
    const size = config.nodeSize[node.type] || config.nodeSize.tool;
    nodeMap.set(node.id, {
      node,
      children: [],
      depth: 0,
      x: 0,
      y: 0,
      width: size.width,
      height: size.height,
      subtreeHeight: 0,
    });
  }

  // 寻找根节点，建立父子关系
  let root: LayoutTreeNode | null = null;
  const orphans: LayoutTreeNode[] = [];

  for (const node of nodes) {
    const layoutNode = nodeMap.get(node.id)!;
    if (node.parentId === undefined || node.parentId === null) {
      // 无 parentId 的节点视为根
      if (!root) {
        root = layoutNode;
      } else {
        // 多个根节点：后续的作为第一个根的子节点
        orphans.push(layoutNode);
      }
    } else {
      const parent = nodeMap.get(node.parentId);
      if (parent) {
        parent.children.push(layoutNode);
      } else {
        // parentId 指向不存在的节点，作为孤儿处理
        orphans.push(layoutNode);
      }
    }
  }

  // 兜底：所有节点都有 parentId 但都指向不存在的节点
  if (!root && nodes.length > 0) {
    root = nodeMap.get(nodes[0].id)!;
  }

  // 将孤儿节点挂载到根节点
  if (root) {
    for (const orphan of orphans) {
      if (orphan !== root) {
        root.children.push(orphan);
      }
    }
  }

  // 递归设置深度
  function setDepth(treeNode: LayoutTreeNode, depth: number): void {
    treeNode.depth = depth;
    for (const child of treeNode.children) {
      setDepth(child, depth + 1);
    }
  }
  if (root) setDepth(root, 0);

  return root;
}

// ============================================================
// 步骤 2：自底向上计算子树高度
// ============================================================

/**
 * 自底向上计算每个节点的子树高度占用
 *
 * 叶子节点：subtreeHeight = 自身 height
 * 有子节点时：subtreeHeight = max(自身 height, 所有子节点 subtreeHeight 之和 + (n-1) * siblingGap)
 */
function computeSubtreeHeights(
  treeNode: LayoutTreeNode,
  config: TopoLayoutConfig
): void {
  if (treeNode.children.length === 0) {
    // 叶子节点：子树高度就是自身高度
    treeNode.subtreeHeight = treeNode.height;
    return;
  }

  // 递归处理所有子节点
  for (const child of treeNode.children) {
    computeSubtreeHeights(child, config);
  }

  // 子节点子树高度总和 + 兄弟间距
  const childrenTotalHeight =
    treeNode.children.reduce((sum, child) => sum + child.subtreeHeight, 0) +
    (treeNode.children.length - 1) * config.spacing.siblingGap;

  // 子树高度取子节点总高和自身高度的最大值
  treeNode.subtreeHeight = Math.max(treeNode.height, childrenTotalHeight);
}

// ============================================================
// 步骤 3：自顶向下分配坐标
// ============================================================

/**
 * 自顶向下分配每个节点的 (x, y) 坐标
 *
 * X 坐标：由层级深度决定，depth * (columnWidth + levelGap)
 * Y 坐标：在分配的子树空间内居中
 */
function assignPositions(
  treeNode: LayoutTreeNode,
  startY: number,
  columnWidth: number,
  config: TopoLayoutConfig
): void {
  const { levelGap, siblingGap } = config.spacing;
  const { left } = config.padding;

  // X 坐标：固定列宽确保各层对齐
  treeNode.x = left + treeNode.depth * (columnWidth + levelGap);

  // Y 坐标：在分配区间 [startY, startY + subtreeHeight) 内居中
  treeNode.y = startY + (treeNode.subtreeHeight - treeNode.height) / 2;

  // 为子节点分配垂直空间
  if (treeNode.children.length > 0) {
    // 子节点总高度（含间距）
    const childrenTotalHeight =
      treeNode.children.reduce((sum, child) => sum + child.subtreeHeight, 0) +
      (treeNode.children.length - 1) * siblingGap;

    // 子节点组在父节点子树空间内居中
    let currentY = startY + (treeNode.subtreeHeight - childrenTotalHeight) / 2;

    for (const child of treeNode.children) {
      assignPositions(child, currentY, columnWidth, config);
      currentY += child.subtreeHeight + siblingGap;
    }
  }
}

// ============================================================
// 步骤 4：收集布局结果并生成连线
// ============================================================

/**
 * 计算两节点之间的水平贝塞尔曲线 SVG path 字符串
 *
 * 起点：源节点右侧中点
 * 终点：目标节点左侧中点
 * 控制点在水平方向偏移，形成流畅的 S 型连线
 */
function computeBezierPath(
  source: LayoutTreeNode,
  target: LayoutTreeNode,
  config: TopoLayoutConfig
): string {
  // 源节点右侧中点
  const sx = source.x + source.width;
  const sy = source.y + source.height / 2;

  // 目标节点左侧中点
  const tx = target.x;
  const ty = target.y + target.height / 2;

  // 水平距离
  const dx = tx - sx;

  // 控制点水平偏移量
  const cpOffset = dx * config.edge.bezierControlRatio;

  // CP1: 从源出发先水平延伸；CP2: 到达目标前水平收回
  const cp1x = sx + cpOffset;
  const cp1y = sy;
  const cp2x = tx - cpOffset;
  const cp2y = ty;

  return `M ${sx} ${sy} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${tx} ${ty}`;
}

/**
 * 遍历树收集所有节点布局和连线路径
 */
function collectLayout(
  root: LayoutTreeNode,
  edges: TopologyEdge[],
  config: TopoLayoutConfig
): LayoutResult {
  const nodeLayouts: NodeLayout[] = [];

  // 建立 id → LayoutTreeNode 映射（遍历一次收集所有节点）
  const posMap = new Map<string, LayoutTreeNode>();

  function collectNodes(tn: LayoutTreeNode): void {
    nodeLayouts.push({
      nodeId: tn.node.id,
      x: tn.x,
      y: tn.y,
      width: tn.width,
      height: tn.height,
    });
    posMap.set(tn.node.id, tn);
    for (const child of tn.children) {
      collectNodes(child);
    }
  }
  collectNodes(root);

  // 根据 edges 数组生成连线路径
  const edgePaths: EdgePath[] = [];
  for (const edge of edges) {
    const src = posMap.get(edge.source);
    const tgt = posMap.get(edge.target);
    // source 或 target 不存在则跳过
    if (!src || !tgt) continue;

    const path = computeBezierPath(src, tgt, config);
    edgePaths.push({
      edgeId: edge.id,
      sourceId: edge.source,
      targetId: edge.target,
      path,
      status: edge.status,
    });
  }

  // 计算画布尺寸
  let maxX = 0;
  let maxY = 0;
  for (const nl of nodeLayouts) {
    maxX = Math.max(maxX, nl.x + nl.width);
    maxY = Math.max(maxY, nl.y + nl.height);
  }

  return {
    nodes: nodeLayouts,
    edges: edgePaths,
    canvasWidth: maxX + config.padding.right,
    canvasHeight: maxY + config.padding.bottom,
  };
}

// ============================================================
// 主入口函数
// ============================================================

/**
 * 水平树状布局算法主入口
 *
 * @param nodes  扁平的拓扑节点数组（通过 parentId 隐含树结构）
 * @param edges  拓扑连线数组
 * @param config 布局配置（可选，默认使用 TOPO_LAYOUT_CONFIG）
 * @returns      布局结果，包含每个节点的坐标和每条连线的 SVG path
 */
export function computeTopoLayout(
  nodes: TopologyNode[],
  edges: TopologyEdge[],
  config: TopoLayoutConfig = TOPO_LAYOUT_CONFIG
): LayoutResult {
  // 步骤 1：构建树
  const root = buildTree(nodes, config);
  if (!root) {
    return { nodes: [], edges: [], canvasWidth: 0, canvasHeight: 0 };
  }

  // 步骤 2：计算子树高度
  computeSubtreeHeights(root, config);

  // 计算统一列宽（取所有节点类型的最大宽度），确保各层对齐美观
  const columnWidth = Math.max(
    ...Object.values(config.nodeSize).map((s) => s.width)
  );

  // 步骤 3：分配坐标
  assignPositions(root, config.padding.top, columnWidth, config);

  // 步骤 4：收集结果并生成连线
  return collectLayout(root, edges, config);
}
