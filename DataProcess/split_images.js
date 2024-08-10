const fs = require('fs');
const path = require('path');

// ===============================检查jpg文件===============================
function checkImages(folderPath, suffix) {
  if (!fs.existsSync(folderPath)) {
    console.log(`Error: Folder "${folderPath}" does not exist.`);
    return false;
  }
  
  const images = fs.readdirSync(folderPath)
    .filter(file => path.extname(file).toLowerCase() === suffix);
  
  if (images.length === 0) {
    console.log(`Error: No .jpg files found in folder "${folderPath}".`);
    return false;
  }
  
  return images;
}

// ===============================配对图片函数===============================
function pairImages(folderPath) {
  const suffix = '.jpg'
  const images = checkImages(folderPath, suffix);
  
  const pairs = [];
  if (!images) {
    console.log(`Warning: 没找到图片`);
    return pairs; // 如果没有图片文件则直接返回空
  }
  // 循环找到图片对
  images.forEach(image => {
    const parts = image.split('-');
    if (parts.length !== 4) {
      console.log(`Warning: "${image}" 不符合图片明明规则`);
    }
    const counterpart = `${parts[0]}-${parts[1]}-G-${parts[3]}`;

    if (images.includes(counterpart)) {
      pairs.push([image, counterpart]);
      images.splice(images.indexOf(counterpart), 1);
    } else {
      console.log(`Warning: No matching “G” file found for "${image}".`);
    }
  });
  return pairs;
}

// ==============================处理“图片对”函数==============================
function pairs_handler(folderPath) {
  const pairs = pairImages(folderPath);
  
  if (pairs.length === 0) {
    console.log('No valid image pairs found. Exiting.');
    return;
  }

  const mergeDir = path.join(folderPath, 'merge');
  
  // 确保merge文件夹存在，如果不存在则创建
  if (!fs.existsSync(mergeDir)) {
    fs.mkdirSync(mergeDir);
  }

  pairs.forEach(([image1, image2]) => {
    console.log(`image1: ${image1}; image2: ${image2}; `);

    const mergedFileName = `Merged_${image1}_${image2}.jpg`;
    const outputPath = path.join(mergeDir, mergedFileName);

    // // 处理&保存图片
    // const result = image_merge(image1, image2, outputPath);
    //   try {
    //   fs.writeFileSync(outputPath, `Merged content of ${image1} and ${image2}`);
    // } catch (error) {
    //   return `Error saving merged image: ${error.message}`;
    // }
    // if (result === true) {
    //   console.log(`Successfully saved merged image: ${outputPath}`);
    // } else {
    //   console.log(result); // 打印错误信息
    // }
  });
}

// 示例调用
const folderPath = './your-folder-path'; // 将 'your-folder-path' 替换为实际的文件夹路径
pairs_handler(folderPath);
