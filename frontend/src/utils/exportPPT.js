import html2canvas from 'html2canvas'
import pptxgen from 'pptxgenjs'

/**
 * 清理元素中的 CSS 颜色函数问题
 */
function cleanColorFunctions(clonedDoc) {
  const allElements = clonedDoc.querySelectorAll('*')
  allElements.forEach(el => {
    try {
      const computedStyle = window.getComputedStyle(el)
      
      const colorProps = ['color', 'backgroundColor', 'borderColor', 'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor']
      
      colorProps.forEach(prop => {
        const value = computedStyle[prop]
        if (value && (value.includes('color(') || value.includes('color-') || value.includes('oklab') || value.includes('oklch'))) {
          if (prop === 'color') el.style.color = '#1F2937'
          else if (prop === 'backgroundColor') el.style.backgroundColor = '#FFFFFF'
          else el.style[prop] = '#D8DEEA'
        }
      })
    } catch (e) {
      // 忽略错误
    }
  })
}

/**
 * 将页面元素导出为 PPT
 * @param {HTMLElement} element - 要导出的 DOM 元素
 * @param {string} title - PPT 标题
 * @param {string} filename - 文件名（不含扩展名）
 */
export async function exportToPPT(element, title, filename = 'dashboard') {
  if (!element) {
    throw new Error('未找到要导出的元素')
  }

  try {
    // 1. 使用 html2canvas 截图
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      logging: false,
      backgroundColor: '#F5F7FB',
      windowWidth: element.scrollWidth,
      windowHeight: element.scrollHeight,
      onclone: (clonedDoc) => {
        cleanColorFunctions(clonedDoc)
      }
    })

    // 2. 转换为 base64 图片
    const imgData = canvas.toDataURL('image/png')

    // 3. 创建 PPT
    const pptx = new pptxgen()
    
    // 设置幻灯片尺寸为 16:9
    pptx.defineLayout({ name: 'CUSTOM', width: 13.33, height: 7.5 })
    pptx.layout = 'CUSTOM'

    // 添加标题页
    let slide1 = pptx.addSlide()
    slide1.addText(title, {
      x: 0.5,
      y: 3,
      w: '90%',
      h: 1,
      fontSize: 36,
      bold: true,
      color: '1F2937',
      align: 'center',
    })
    slide1.addText(new Date().toLocaleDateString('zh-CN', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }), {
      x: 0.5,
      y: 4.2,
      w: '90%',
      h: 0.5,
      fontSize: 18,
      color: '6B7280',
      align: 'center',
    })

    // 添加内容页 - 图片填满整个页面
    const slide2 = pptx.addSlide()
    
    // PPT 页面尺寸 (16:9)
    const slideWidth = 13.33
    const slideHeight = 7.5
    
    // 图片填满整个页面，不留边距
    slide2.addImage({
      data: imgData,
      x: 0,
      y: 0,
      w: slideWidth,
      h: slideHeight,
      sizing: { type: 'cover', w: slideWidth, h: slideHeight }
    })

    // 4. 导出文件
    const pptxBlob = await pptx.write({ outputType: 'blob' })
    
    // 创建下载链接
    const url = URL.createObjectURL(pptxBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.pptx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    return true
  } catch (error) {
    console.error('导出 PPT 失败:', error)
    throw error
  }
}

/**
 * 简化版：直接截图当前页面并导出
 * @param {string} title - 标题
 */
export async function exportCurrentPage(title) {
  const element = document.querySelector('.page')
  if (!element) {
    throw new Error('未找到页面元素')
  }
  
  const timestamp = new Date().toISOString().slice(0, 10)
  const filename = `${title}_${timestamp}`
  
  return exportToPPT(element, title, filename)
}
