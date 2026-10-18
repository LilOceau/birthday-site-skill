/* Fictional fixture for the read-only inspector; no personal content. */
window.BIRTHDAY_CONTENT = {
  hintYear: 2026,
  memories: [{
    date: '06/15',
    title: '示例日期',
    photos: [
      {src: 'assets/card-a.svg?v=example#preview', thumb: 'assets/card-a.svg', original: 'assets/card-a.svg', type: 'image', caption: '示例图形 1'},
      {src: 'assets/card-b.svg', thumb: 'assets/card-b.svg', original: 'assets/card-b.svg', type: 'image', caption: '示例图形 2'}
    ]
  }],
  collage: [{
    src: 'assets/card-a.svg', preview: 'assets/card-a.svg', thumb: 'assets/card-a.svg',
    caption: '示例拼贴 01', width: 600, height: 800
  }],
  quiz: [{
    question: '这个示例相册有几张静态图片？',
    options: ['一张', '两张', '三张', '四张'],
    answer: 1,
    explanation: '示例相册引用了两张自制 SVG 图形。'
  }]
};
