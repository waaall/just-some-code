// [RGB merge](https://imagej.net/imaging/color-image-processing)

import ij.IJ;
import ij.ImagePlus;
import ij.io.FileSaver;
import ij.process.ImageProcessor;
import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class MergeRGs {

    public static void pairs_handler(String[] args) {
        // 初始化 ImageJ
        IJ.init();

        // 指定图片文件夹路径
        String folderPath = "path/to/your/folder";  // 替换为实际的文件夹路径

        // 获取图片配对
        List<String[]> pairs = findImagePairs(folderPath);

        if (pairs.isEmpty()) {
            System.out.println("No valid image pairs found. Exiting.");
            return;
        }

        // 创建保存合并图像的目录
        File mergeDir = new File(folderPath, "merge");
        if (!mergeDir.exists()) {
            mergeDir.mkdirs();
        }

        // 处理每对图片
        for (String[] pair : pairs) {
            String image1Path = new File(folderPath, pair[0]).getAbsolutePath();
            String image2Path = new File(folderPath, pair[1]).getAbsolutePath();
            String mergedImagePath = new File(mergeDir, "Merged_" + pair[0] + "_" + pair[1] + ".jpg").getAbsolutePath();

            try {
                mergeAndSaveImages(image1Path, image2Path, mergedImagePath);
                System.out.println("Successfully saved merged image: " + mergedImagePath);
            } catch (Exception e) {
                System.err.println("Error saving merged image: " + e.getMessage());
            }
        }

        System.out.println("Processing completed.");
    }

    private static List<String[]> findImagePairs(String folderPath) {
        File folder = new File(folderPath);
        File[] imageFiles = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".jpg"));

        if (imageFiles == null || imageFiles.length == 0) {
            System.out.println("No .jpg files found in folder \"" + folderPath + "\".");
            return new ArrayList<>();
        }

        Set<String> imageSet = new HashSet<>();
        for (File file : imageFiles) {
            imageSet.add(file.getName());
        }

        List<String[]> pairs = new ArrayList<>();
        for (String image : imageSet) {
            String[] parts = image.split("-");
            if (parts.length != 4) {
                System.out.println("Warning: File \"" + image + "\" does not match the expected naming pattern.");
                continue;
            }

            String counterpart = parts[0] + "-" + parts[1] + "-G-" + parts[3];
            if (imageSet.contains(counterpart)) {
                pairs.add(new String[]{image, counterpart});
                imageSet.remove(counterpart);  // Avoid duplicate pairing
            }
        }

        return pairs;
    }

    private static void mergeAndSaveImages(String image1Path, String image2Path, String outputPath) {
        // 打开图像
        ImagePlus imp1 = IJ.openImage(image1Path);
        ImagePlus imp2 = IJ.openImage(image2Path);

        if (imp1 == null || imp2 == null) {
            throw new IllegalArgumentException("One or both images could not be opened.");
        }

        // 合并图像
        ImageProcessor ip1 = imp1.getProcessor();
        ImageProcessor ip2 = imp2.getProcessor();
        int width = Math.max(ip1.getWidth(), ip2.getWidth());
        int height = Math.max(ip1.getHeight(), ip2.getHeight());

        // 创建一个新的图像来存储合并结果
        ImagePlus mergedImage = IJ.createImage("Merged", "RGB", width, height, 2);
        ImageProcessor mergedIP = mergedImage.getProcessor();

        // 合并两个通道
        mergedIP.copyBits(ip1, 0, 0, ImageProcessor.RED_LUT);
        mergedIP.copyBits(ip2, 0, 0, ImageProcessor.GREEN_LUT);

        // 保存合并后的图像
        FileSaver fs = new FileSaver(mergedImage);
        boolean success = fs.saveAsJpeg(outputPath);
        if (!success) {
            throw new RuntimeException("Failed to save merged image.");
        }
    }
}