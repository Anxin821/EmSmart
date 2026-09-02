/**
 * PPT导出工具
 * 使用 pptxgenjs 生成PPT文件
 */
import pptxgen from 'pptxgenjs'

/**
 * 创建PPT演示文稿
 * @param {string} title - 演示文稿标题
 * @returns {pptxgen} PPT实例
 */
export function createPresentation(title) {
  const pptx = new pptxgen()
  pptx.layout = 'LAYOUT_WIDE'
  pptx.title = title
  pptx.author = 'EmSmart System'
  pptx.subject = 'Dashboard Report'
  return pptx
}

/**
 * 添加标题页
 * @param {pptxgen} pptx - PPT实例
 * @param {string} title - 标题
 * @param {string} subtitle - 副标题（可选）
 */
export function addTitleSlide(pptx, title, subtitle = '') {
  const slide = pptx.addSlide()
  slide.background = { color: 'FFFFFF' }
  
  // 标题
  slide.addText(title, {
    x: 0.5,
    y: 2.5,
    w: 9,
    h: 1,
    fontSize: 44,
    bold: true,
    color: '1F2937',
    align: 'center'
  })
  
  // 副标题
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5,
      y: 3.5,
      w: 9,
      h: 0.5,
      fontSize: 20,
      color: '6B7280',
      align: 'center'
    })
  }
  
  // 日期
  const date = new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
  slide.addText(date, {
    x: 0.5,
    y: 4.2,
    w: 9,
    h: 0.4,
    fontSize: 16,
    color: '9CA3AF',
    align: 'center'
  })
}

/**
 * 添加统计指标页
 * @param {pptxgen} pptx - PPT实例
 * @param {string} title - 页面标题
 * @param {Array} stats - 统计数据数组 [{label, value, color}]
 */
export function addStatsSlide(pptx, title, stats) {
  const slide = pptx.addSlide()
  slide.background = { color: 'FFFFFF' }
  
  // 页面标题
  slide.addText(title, {
    x: 0.5,
    y: 0.3,
    w: 9,
    h: 0.5,
    fontSize: 24,
    bold: true,
    color: '1F2937'
  })
  
  // 计算每个统计卡片的宽度
  const cardWidth = stats.length > 0 ? (9 - 0.5 * (stats.length - 1)) / stats.length : 2
  const startX = 0.5
  const cardHeight = 1.8
  
  stats.forEach((stat, index) => {
    const x = startX + index * (cardWidth + 0.5)
    
    // 卡片背景
    slide.addShape(pptx.ShapeType.rect, {
      x: x,
      y: 1.2,
      w: cardWidth,
      h: cardHeight,
      fill: { color: 'F9FAFB' },
      line: { color: 'E5E7EB', width: 1 }
    })
    
    // 数值
    slide.addText(String(stat.value), {
      x: x,
      y: 1.5,
      w: cardWidth,
      h: 0.9,
      fontSize: 42,
      bold: true,
      color: stat.color || '3B82F6',
      align: 'center'
    })
    
    // 标签
    slide.addText(stat.label, {
      x: x,
      y: 2.5,
      w: cardWidth,
      h: 0.4,
      fontSize: 14,
      color: '6B7280',
      align: 'center'
    })
  })
}

/**
 * 添加图表页（使用截图）
 * @param {pptxgen} pptx - PPT实例
 * @param {string} title - 页面标题
 * @param {string} imageData - base64图片数据
 */
export function addChartSlide(pptx, title, imageData) {
  const slide = pptx.addSlide()
  slide.background = { color: 'FFFFFF' }
  
  // 页面标题
  slide.addText(title, {
    x: 0.5,
    y: 0.3,
    w: 9,
    h: 0.5,
    fontSize: 24,
    bold: true,
    color: '1F2937'
  })
  
  // 图表图片
  if (imageData) {
    slide.addImage({
      data: imageData,
      x: 0.5,
      y: 1,
      w: 9,
      h: 4
    })
  }
}

/**
 * 添加表格页
 * @param {pptxgen} pptx - PPT实例
 * @param {string} title - 页面标题
 * @param {Array} headers - 表头
 * @param {Array} rows - 表格数据
 * @param {Object} options - 配置选项
 */
export function addTableSlide(pptx, title, headers, rows, options = {}) {
  const slide = pptx.addSlide()
  slide.background = { color: 'FFFFFF' }
  
  // 页面标题
  slide.addText(title, {
    x: 0.5,
    y: 0.3,
    w: 9,
    h: 0.5,
    fontSize: 24,
    bold: true,
    color: '1F2937'
  })
  
  // 表格
  const tableData = [headers, ...rows]
  slide.addTable(tableData, {
    x: 0.5,
    y: 1,
    w: 9,
    colW: options.colW || headers.map(() => 9 / headers.length),
    border: { type: 'solid', pt: 1, color: 'E5E7EB' },
    fontFace: 'Microsoft YaHei',
    fontSize: 12,
    color: '1F2937',
    align: 'center',
    valign: 'middle',
    rowH: options.rowH || 0.4,
    fill: { color: 'FFFFFF' }
  })
}

/**
 * 添加卡片列表页
 * @param {pptxgen} pptx - PPT实例
 * @param {string} title - 页面标题
 * @param {Array} cards - 卡片数据数组
 * @param {number} cols - 列数
 */
export function addCardsSlide(pptx, title, cards, cols = 6) {
  const slide = pptx.addSlide()
  slide.background = { color: 'FFFFFF' }
  
  // 页面标题
  slide.addText(title, {
    x: 0.5,
    y: 0.3,
    w: 9,
    h: 0.5,
    fontSize: 24,
    bold: true,
    color: '1F2937'
  })
  
  // 计算卡片尺寸
  const gap = 0.15
  const cardWidth = (9 - gap * (cols - 1)) / cols
  const cardHeight = 0.8
  const startX = 0.5
  const startY = 1
  
  cards.forEach((card, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    const x = startX + col * (cardWidth + gap)
    const y = startY + row * (cardHeight + gap)
    
    // 卡片背景
    slide.addShape(pptx.ShapeType.rect, {
      x: x,
      y: y,
      w: cardWidth,
      h: cardHeight,
      fill: { color: card.bgColor || 'FEF2F2' },
      line: { color: card.borderColor || 'FECACA', width: 1 }
    })
    
    // 卡片内容
    if (card.text) {
      slide.addText(card.text, {
        x: x + 0.1,
        y: y + 0.15,
        w: cardWidth - 0.2,
        h: cardHeight - 0.3,
        fontSize: 11,
        color: card.textColor || '1F2937',
        align: 'left',
        valign: 'middle'
      })
    }
  })
}

/**
 * 添加整屏截图页（图片等比 contain 铺满单页，不变形）
 * @param {pptxgen} pptx - PPT实例
 * @param {string} imageData - base64图片数据
 */
export function addFullImageSlide(pptx, imageData) {
  const slide = pptx.addSlide()
  slide.background = { color: 'FFFFFF' }
  if (imageData) {
    slide.addImage({
      data: imageData,
      x: 0,
      y: 0,
      w: 13.33,
      h: 7.5,
      sizing: { type: 'contain', w: 13.33, h: 7.5 }
    })
  }
}

/**
 * 保存PPT文件
 * @param {pptxgen} pptx - PPT实例
 * @param {string} filename - 文件名
 */
export function savePresentation(pptx, filename) {
  pptx.writeFile({ fileName: filename })
}

/**
 * 截图DOM元素为base64图片
 * @param {string} elementId - DOM元素ID
 * @returns {Promise<string>} base64图片数据
 */
export async function captureElement(elementId) {
  const element = document.getElementById(elementId)
  if (!element) {
    console.warn(`Element with id "${elementId}" not found`)
    return null
  }
  
  // 动态导入 html2canvas
  const html2canvas = (await import('html2canvas')).default
  
  const canvas = await html2canvas(element, {
    backgroundColor: '#ffffff',
    scale: 2
  })
  
  return canvas.toDataURL('image/png')
}

/**
 * 颜色映射
 */
export const colorMap = {
  blue: '3B82F6',
  green: '10B981',
  red: 'EF4444',
  yellow: 'F59E0B',
  purple: '8B5CF6',
  cyan: '06B6D4',
  pink: 'EC4899',
  gray: '6B7280'
}
