package com.thesysm.mdetect.camera

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import androidx.camera.core.ImageProxy
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer

fun imageProxyToOptimizedJpeg(image: ImageProxy, maxLongSide: Int = 1280, quality: Int = 80): ByteArray? {
    return runCatching {
        val nv21 = imageProxyToNv21(image)
        val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
        val rawJpeg = ByteArrayOutputStream()
        yuvImage.compressToJpeg(Rect(0, 0, image.width, image.height), quality, rawJpeg)
        val bitmap = BitmapFactory.decodeByteArray(rawJpeg.toByteArray(), 0, rawJpeg.size())
        val rotated = rotateBitmap(bitmap, image.imageInfo.rotationDegrees)
        val resized = resizeLongSide(rotated, maxLongSide)
        val output = ByteArrayOutputStream()
        resized.compress(Bitmap.CompressFormat.JPEG, quality, output)
        if (resized !== rotated) resized.recycle()
        if (rotated !== bitmap) rotated.recycle()
        bitmap.recycle()
        output.toByteArray()
    }.getOrNull()
}

private fun imageProxyToNv21(image: ImageProxy): ByteArray {
    val width = image.width
    val height = image.height
    val yPlane = image.planes[0]
    val uPlane = image.planes[1]
    val vPlane = image.planes[2]
    val nv21 = ByteArray(width * height * 3 / 2)

    copyPlaneToBytes(
        buffer = yPlane.buffer,
        rowStride = yPlane.rowStride,
        pixelStride = yPlane.pixelStride,
        width = width,
        height = height,
        output = nv21,
        outputOffset = 0,
        outputPixelStride = 1
    )

    val chromaHeight = height / 2
    val chromaWidth = width / 2
    copyPlaneToBytes(
        buffer = vPlane.buffer,
        rowStride = vPlane.rowStride,
        pixelStride = vPlane.pixelStride,
        width = chromaWidth,
        height = chromaHeight,
        output = nv21,
        outputOffset = width * height,
        outputPixelStride = 2
    )
    copyPlaneToBytes(
        buffer = uPlane.buffer,
        rowStride = uPlane.rowStride,
        pixelStride = uPlane.pixelStride,
        width = chromaWidth,
        height = chromaHeight,
        output = nv21,
        outputOffset = width * height + 1,
        outputPixelStride = 2
    )
    return nv21
}

private fun copyPlaneToBytes(
    buffer: ByteBuffer,
    rowStride: Int,
    pixelStride: Int,
    width: Int,
    height: Int,
    output: ByteArray,
    outputOffset: Int,
    outputPixelStride: Int
) {
    val duplicate = buffer.duplicate()
    for (row in 0 until height) {
        for (col in 0 until width) {
            val inputIndex = row * rowStride + col * pixelStride
            val outputIndex = outputOffset + row * width * outputPixelStride + col * outputPixelStride
            if (inputIndex < duplicate.limit() && outputIndex < output.size) {
                output[outputIndex] = duplicate.get(inputIndex)
            }
        }
    }
}

private fun rotateBitmap(bitmap: Bitmap, rotationDegrees: Int): Bitmap {
    if (rotationDegrees == 0) return bitmap
    val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
    return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
}

private fun resizeLongSide(bitmap: Bitmap, maxLongSide: Int): Bitmap {
    val longSide = maxOf(bitmap.width, bitmap.height)
    if (longSide <= maxLongSide) return bitmap
    val scale = maxLongSide.toFloat() / longSide.toFloat()
    val width = (bitmap.width * scale).toInt().coerceAtLeast(1)
    val height = (bitmap.height * scale).toInt().coerceAtLeast(1)
    return Bitmap.createScaledBitmap(bitmap, width, height, true)
}
