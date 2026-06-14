package com.thesysm.mdetect.ui

import android.Manifest
import android.graphics.Paint
import android.util.Log
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.thesysm.mdetect.AppScreen
import com.thesysm.mdetect.AppUiState
import com.thesysm.mdetect.MDetectViewModel
import com.thesysm.mdetect.R
import com.thesysm.mdetect.camera.imageProxyToOptimizedJpeg
import com.thesysm.mdetect.model.AppSettings
import com.thesysm.mdetect.model.DetectionBox
import com.thesysm.mdetect.model.DetectionMode
import java.util.concurrent.Executors

@Composable
fun MDetectApp(viewModel: MDetectViewModel) {
    val state by viewModel.uiState.collectAsState()
    when (state.screen) {
        AppScreen.SPLASH -> SplashScreen(state)
        AppScreen.LANDING -> LandingScreen(state, viewModel)
        AppScreen.LOGIN -> LoginScreen(state, viewModel)
        AppScreen.SIGN_UP -> SignUpScreen(state, viewModel)
        AppScreen.HOME -> HomeScreen(state, viewModel)
        AppScreen.CAMERA -> CameraDetectionScreen(state, viewModel)
        AppScreen.HISTORY -> DetectionHistoryScreen(state, viewModel)
        AppScreen.MODEL_UPDATE -> ModelUpdateScreen(state, viewModel)
        AppScreen.SETTINGS -> SettingsScreen(state, viewModel)
    }
}

@Composable
private fun LandingScreen(state: AppUiState, viewModel: MDetectViewModel) {
    val background = Color(0xFFF7F2EA)
    val surface = Color(0xFFFFFDF8)
    val primaryText = Color(0xFF2F2A25)
    val secondaryText = Color(0xFF7A7168)
    val sage = Color(0xFFAEBBAA)
    val rose = Color(0xFFE6A1AE)
    val deepOlive = Color(0xFF4F5B4A)

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(background)
            .statusBarsPadding()
            .navigationBarsPadding()
            .padding(horizontal = 24.dp, vertical = 18.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .widthIn(max = 520.dp)
                .align(Alignment.Center),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("MDetect", color = primaryText, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                    Text("Mobile Detection Console", color = secondaryText, style = MaterialTheme.typography.labelLarge)
                }
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(CircleShape)
                        .background(sage),
                    contentAlignment = Alignment.Center
                ) {
                    Text("AI", color = deepOlive, fontWeight = FontWeight.Bold)
                }
            }

            Spacer(Modifier.height(24.dp))

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 390.dp)
                    .aspectRatio(0.78f)
                    .clip(RoundedCornerShape(28.dp))
                    .background(surface)
                    .border(1.dp, Color(0x22A27C6F), RoundedCornerShape(28.dp))
            ) {
                Image(
                    painter = painterResource(R.drawable.mdetect_landing_image),
                    contentDescription = "MDetect landing image",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(Color.Transparent, Color(0xCC2F2A25)),
                                startY = 260f
                            )
                        )
                )
                Column(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(22.dp)
                ) {
                    Text("Server Mode Ready", color = Color.White, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text(
                        state.authStatus,
                        color = Color(0xFFEDE7DD),
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }

            Spacer(Modifier.height(24.dp))

            Text(
                "버려지는 아름다움을\n객체탐지 데이터로 연결",
                color = primaryText,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(10.dp))
            Text(
                "카메라로 용기와 물체를 확인하고,\n서버 모델로 탐지 결과를 기록합니다.",
                color = secondaryText,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.weight(1f))

            LandingPillButton(
                text = "로그인",
                background = Brush.horizontalGradient(listOf(rose, sage)),
                textColor = primaryText,
                onClick = { viewModel.navigate(AppScreen.LOGIN) }
            )
            Spacer(Modifier.height(10.dp))
            LandingPillButton(
                text = "회원가입",
                background = Brush.horizontalGradient(listOf(surface, Color(0xFFF3E1E5))),
                textColor = primaryText,
                onClick = { viewModel.navigate(AppScreen.SIGN_UP) }
            )
            Spacer(Modifier.height(12.dp))
            LandingPillButton(
                text = "서버 설정",
                background = Brush.horizontalGradient(listOf(surface, Color(0xFFEDE7DD))),
                textColor = deepOlive,
                onClick = { viewModel.navigate(AppScreen.SETTINGS) }
            )
        }
    }
}

@Composable
private fun LoginScreen(state: AppUiState, viewModel: MDetectViewModel) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    AuthScreenShell(title = "로그인", state = state) {
        AuthTextField(
            value = username,
            onValueChange = { username = it },
            label = "Username"
        )
        AuthTextField(
            value = password,
            onValueChange = { password = it },
            label = "Password",
            visualTransformation = PasswordVisualTransformation()
        )
        Button(
            onClick = { viewModel.login(username.trim(), password) },
            modifier = Modifier.fillMaxWidth().height(52.dp),
            shape = RoundedCornerShape(16.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2F5D50), contentColor = Color.White)
        ) { Text("로그인") }
        TextButton(onClick = { viewModel.navigate(AppScreen.SIGN_UP) }, modifier = Modifier.fillMaxWidth()) {
            Text("회원가입")
        }
        TextButton(onClick = { viewModel.navigate(AppScreen.LANDING) }, modifier = Modifier.fillMaxWidth()) {
            Text("처음 화면")
        }
    }
}

@Composable
private fun SignUpScreen(state: AppUiState, viewModel: MDetectViewModel) {
    var username by remember { mutableStateOf("") }
    var phoneNumber by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    AuthScreenShell(title = "회원가입", state = state) {
        AuthTextField(value = username, onValueChange = { username = it }, label = "Username")
        AuthTextField(value = phoneNumber, onValueChange = { phoneNumber = it }, label = "Phone number")
        AuthTextField(value = password, onValueChange = { password = it }, label = "Password", visualTransformation = PasswordVisualTransformation())
        AuthTextField(value = confirmPassword, onValueChange = { confirmPassword = it }, label = "Confirm password", visualTransformation = PasswordVisualTransformation())
        Button(
            onClick = { viewModel.signup(username.trim(), phoneNumber.trim(), password, confirmPassword) },
            modifier = Modifier.fillMaxWidth().height(52.dp),
            shape = RoundedCornerShape(16.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2F5D50), contentColor = Color.White)
        ) { Text("가입 신청") }
        TextButton(onClick = { viewModel.navigate(AppScreen.LOGIN) }, modifier = Modifier.fillMaxWidth()) {
            Text("로그인으로 돌아가기")
        }
    }
}

@Composable
private fun AuthScreenShell(title: String, state: AppUiState, content: @Composable ColumnScope.() -> Unit) {
    val background = Color(0xFFF7F2EA)
    val primaryText = Color(0xFF2F2A25)
    val secondaryText = Color(0xFF6F665E)
    val accent = Color(0xFF2F5D50)
    Surface(modifier = Modifier.fillMaxSize(), color = background) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 28.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Column(
                modifier = Modifier.widthIn(max = 520.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Box(
                    modifier = Modifier
                        .size(58.dp)
                        .clip(CircleShape)
                        .background(Color(0xFFAEBBAA)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("AI", color = accent, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.height(14.dp))
                Text("MDetect", color = primaryText, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
                Text(title, color = secondaryText, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(22.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(28.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFFDF8)),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp),
                        content = content
                    )
                }
                if (state.authMessage.isNotBlank()) {
                    Spacer(Modifier.height(16.dp))
                    Text(state.authMessage, textAlign = TextAlign.Center, color = accent, style = MaterialTheme.typography.bodyMedium)
                }
                Spacer(Modifier.height(8.dp))
                Text("Status: ${state.authStatus}", color = secondaryText, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun AuthTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    visualTransformation: androidx.compose.ui.text.input.VisualTransformation = androidx.compose.ui.text.input.VisualTransformation.None
) {
    val textColor = Color(0xFF2F2A25)
    val labelColor = Color(0xFF6F665E)
    val borderColor = Color(0xFFD8CEC4)
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
        visualTransformation = visualTransformation,
        shape = RoundedCornerShape(16.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedTextColor = textColor,
            unfocusedTextColor = textColor,
            cursorColor = Color(0xFF2F5D50),
            focusedContainerColor = Color.White,
            unfocusedContainerColor = Color.White,
            focusedBorderColor = Color(0xFF2F5D50),
            unfocusedBorderColor = borderColor,
            focusedLabelColor = Color(0xFF2F5D50),
            unfocusedLabelColor = labelColor
        )
    )
}

@Composable
private fun LandingPillButton(text: String, background: Brush, textColor: Color, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(58.dp)
            .clip(CircleShape)
            .background(background)
            .border(1.dp, Color(0x33000000), CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(text, color = textColor, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun SplashScreen(state: AppUiState) {
    Surface(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier.fillMaxSize().padding(32.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("MDetect", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            Text(if (state.loading) "Starting..." else state.detectionStatus)
        }
    }
}

@Composable
private fun AppShell(title: String, state: AppUiState, viewModel: MDetectViewModel, content: @Composable () -> Unit) {
    Scaffold(
        bottomBar = {
            Row(
                modifier = Modifier.fillMaxWidth().navigationBarsPadding().padding(8.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TextButton(onClick = { viewModel.navigate(AppScreen.HOME) }) { Text("Home") }
                TextButton(onClick = { viewModel.navigate(AppScreen.CAMERA) }) { Text("Camera") }
                TextButton(onClick = { viewModel.navigate(AppScreen.MODEL_UPDATE) }) { Text("Model") }
                TextButton(onClick = { viewModel.navigate(AppScreen.SETTINGS) }) { Text("Settings") }
            }
        }
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(state.networkStatus, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
            Spacer(Modifier.height(16.dp))
            content()
        }
    }
}

@Composable
private fun HomeScreen(state: AppUiState, viewModel: MDetectViewModel) {
    var showLogoutDialog by remember { mutableStateOf(false) }
    if (showLogoutDialog) {
        ConfirmLogoutDialog(
            onDismiss = { showLogoutDialog = false },
            onConfirm = {
                showLogoutDialog = false
                viewModel.logout()
            }
        )
    }
    AppShell("MDetect", state, viewModel) {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item {
                InfoCard("Auth Status", state.authStatus)
                if (state.authUser.username.isNotBlank()) {
                    InfoCard("User", "${state.authUser.username} / ${state.authUser.phoneNumber}")
                }
                if (state.authMessage.isNotBlank()) {
                    InfoCard("Welcome", state.authMessage)
                }
                InfoCard("Server URL", state.settings.serverUrl)
                InfoCard("Detection Mode", state.settings.detectionMode.name)
                InfoCard("Model Version", state.modelMetadata.modelVersion)
                InfoCard("Server Status", state.serverStatus)
            }
            item { Button(onClick = { viewModel.navigate(AppScreen.CAMERA) }, modifier = Modifier.fillMaxWidth()) { Text("Start Camera Detection") } }
            item { Button(onClick = { viewModel.navigate(AppScreen.MODEL_UPDATE) }, modifier = Modifier.fillMaxWidth()) { Text("Model Update") } }
            item { Button(onClick = { viewModel.navigate(AppScreen.HISTORY) }, modifier = Modifier.fillMaxWidth()) { Text("Detection History") } }
            item { Button(onClick = { viewModel.navigate(AppScreen.SETTINGS) }, modifier = Modifier.fillMaxWidth()) { Text("Settings") } }
            item {
                Button(
                    onClick = { showLogoutDialog = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF991B1B), contentColor = Color.White)
                ) { Text("로그아웃") }
            }
        }
    }
}

@Composable
private fun ConfirmLogoutDialog(onDismiss: () -> Unit, onConfirm: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("로그아웃하시겠습니까?") },
        text = { Text("저장된 세션 정보가 삭제되고 다시 로그인해야 합니다.") },
        confirmButton = {
            TextButton(onClick = onConfirm) { Text("로그아웃") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("취소") }
        }
    )
}

@Composable
private fun InfoCard(label: String, value: String) {
    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(14.dp)) {
            Text(label, style = MaterialTheme.typography.labelMedium)
            Text(value, style = MaterialTheme.typography.bodyLarge)
        }
    }
    Spacer(Modifier.height(8.dp))
}

@Composable
private fun CameraDetectionScreen(state: AppUiState, viewModel: MDetectViewModel) {
    val context = LocalContext.current
    val uriHandler = LocalUriHandler.current
    var hasPermission by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED)
    }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted -> hasPermission = granted }
    LaunchedEffect(Unit) {
        if (!hasPermission) launcher.launch(Manifest.permission.CAMERA)
    }

    Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
        if (hasPermission) {
            CameraPreview(
                frameIntervalMs = state.settings.frameIntervalMs,
                detecting = state.detecting,
                onFrame = viewModel::processFrame
            )
        } else {
            Text("Camera permission is required", modifier = Modifier.align(Alignment.Center), color = Color.White)
        }
        DetectionOverlay(
            detections = state.detections,
            modifier = Modifier.fillMaxSize(),
            onLabelClick = { box ->
                if (detectionLabelHasLink(box)) {
                    uriHandler.openUri("https://www.rafarophe.com/")
                }
            }
        )
        if (state.cameraStatusOverlayVisible) {
            CameraStatusPanel(state, Modifier.align(Alignment.TopCenter).padding(12.dp))
        }
        Row(
            modifier = Modifier.align(Alignment.BottomCenter).navigationBarsPadding().padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(9.dp)
        ) {
            Button(
                onClick = { viewModel.setDetecting(!state.detecting) },
                contentPadding = PaddingValues(horizontal = 23.dp, vertical = 7.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (state.detecting) Color(0xFFDC2626) else Color(0xFF2563EB),
                    contentColor = Color.White
                )
            ) {
                Text(if (state.detecting) "STOP" else "START", fontSize = 12.sp)
            }
            Button(
                onClick = viewModel::toggleCameraStatusOverlay,
                contentPadding = PaddingValues(horizontal = 15.dp, vertical = 7.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xCC111827),
                    contentColor = Color.White
                )
            ) {
                Text(if (state.cameraStatusOverlayVisible) "Hide" else "Show", fontSize = 12.sp)
            }
            Button(
                onClick = { viewModel.navigate(AppScreen.HOME) },
                contentPadding = PaddingValues(horizontal = 23.dp, vertical = 7.dp)
            ) {
                Text("Back", fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun CameraStatusPanel(state: AppUiState, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xCC111827)),
        shape = RoundedCornerShape(10.dp)
    ) {
        Column(Modifier.padding(12.dp)) {
            Text("Mode: ${state.settings.detectionMode.name}", color = Color.White)
            Text(
                "Detection: ${if (state.detecting) "RUNNING" else "STOPPED"}",
                color = if (state.detecting) Color(0xFF86EFAC) else Color(0xFFFCA5A5),
                fontWeight = FontWeight.Bold
            )
            Text("Model: ${state.modelMetadata.modelVersion}", color = Color.White)
            Text("FPS: ${"%.1f".format(state.fps)}  Latency: ${state.latencyMs} ms", color = Color.White)
            Text("Network: ${state.networkStatus}", color = Color.White)
            Text("Objects: ${state.detections.size}  Threshold: ${state.settings.confidenceThreshold}", color = Color.White)
            if (state.settings.detectionMode == DetectionMode.ON_DEVICE) {
                Text("Local files: ${state.modelFileState.summary}", color = Color.White)
                Text("Input: ${compactDebug(state.onDeviceDebug.inputShape)} ${state.onDeviceDebug.inputDtype}", color = Color.White)
                Text("Output: ${compactDebug(state.onDeviceDebug.outputShapes)}", color = Color.White)
                Text("Layout: ${compactDebug(state.onDeviceDebug.decoderLayout)}", color = Color.White)
                if (state.onDeviceDebug.lastError.isNotBlank()) {
                    Text("Last error: ${compactDebug(state.onDeviceDebug.lastError)}", color = Color(0xFFFCA5A5))
                }
            }
            Text(state.detectionStatus, color = Color(0xFFFBBF24))
        }
    }
}

@Composable
private fun CameraPreview(frameIntervalMs: Long, detecting: Boolean, onFrame: (ByteArray) -> Unit) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val currentDetecting by rememberUpdatedState(detecting)
    val currentOnFrame by rememberUpdatedState(onFrame)
    var lastSent by remember { mutableLongStateOf(0L) }
    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { ctx ->
            val previewView = PreviewView(ctx)
            val providerFuture = ProcessCameraProvider.getInstance(ctx)
            providerFuture.addListener({
                val provider = providerFuture.get()
                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }
                val analyzer = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()
                    .also { analysis ->
                        analysis.setAnalyzer(Executors.newSingleThreadExecutor()) { image ->
                            val now = System.currentTimeMillis()
                            if (currentDetecting && now - lastSent >= frameIntervalMs) {
                                lastSent = now
                                val jpeg = imageProxyToOptimizedJpeg(image)
                                if (jpeg == null) {
                                    Log.w("MDetectCamera", "Frame JPEG conversion failed width=${image.width} height=${image.height}")
                                } else {
                                    Log.d("MDetectCamera", "Frame sent bytes=${jpeg.size} width=${image.width} height=${image.height}")
                                    currentOnFrame(jpeg)
                                }
                            }
                            image.close()
                        }
                    }
                provider.unbindAll()
                provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, analyzer)
            }, ContextCompat.getMainExecutor(context))
            previewView
        }
    )
}

private data class LabelHitRect(
    val left: Float,
    val top: Float,
    val right: Float,
    val bottom: Float
) {
    fun contains(offset: Offset): Boolean =
        offset.x in left..right && offset.y in top..bottom
}

private fun detectionLabelText(box: DetectionBox): String =
    box.className.ifBlank { "class_${box.classId}" }

private fun detectionLabelHasLink(box: DetectionBox): Boolean =
    !box.className.trim().equals("other", ignoreCase = true)

private fun detectionLabelBounds(
    box: DetectionBox,
    canvasWidth: Float,
    canvasHeight: Float,
    labelWidth: Float,
    labelHeight: Float
): LabelHitRect {
    val scaleX = canvasWidth / maxOf(1, box.imageWidth)
    val scaleY = canvasHeight / maxOf(1, box.imageHeight)
    val boxLeft = box.xMin * scaleX
    val boxTop = box.yMin * scaleY
    val labelLeft = boxLeft.coerceIn(0f, maxOf(0f, canvasWidth - labelWidth))
    val labelTop = if (boxTop >= labelHeight + 6f) {
        boxTop - labelHeight - 6f
    } else {
        (boxTop + 6f).coerceAtMost(maxOf(0f, canvasHeight - labelHeight))
    }
    return LabelHitRect(labelLeft, labelTop, labelLeft + labelWidth, labelTop + labelHeight)
}

@Composable
private fun DetectionOverlay(
    detections: List<DetectionBox>,
    modifier: Modifier = Modifier,
    onLabelClick: (DetectionBox) -> Unit = {}
) {
    Canvas(
        modifier = modifier.pointerInput(detections) {
            detectTapGestures { offset ->
                val labelHeight = 28.dp.toPx()
                detections.asReversed().firstOrNull { box ->
                    if (!detectionLabelHasLink(box)) {
                        return@firstOrNull false
                    }
                    val label = detectionLabelText(box)
                    val labelWidth = maxOf(76.dp.toPx(), label.length * 8.dp.toPx() + 24.dp.toPx())
                    detectionLabelBounds(
                        box = box,
                        canvasWidth = size.width.toFloat(),
                        canvasHeight = size.height.toFloat(),
                        labelWidth = labelWidth,
                        labelHeight = labelHeight
                    ).contains(offset)
                }?.let(onLabelClick)
            }
        }
    ) {
        val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.White.toArgb()
            textSize = 13.sp.toPx()
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        }
        detections.forEachIndexed { index, box ->
            val color = listOf(Color.Cyan, Color.Green, Color.Yellow, Color.Magenta)[index % 4]
            val scaleX = size.width / maxOf(1, box.imageWidth)
            val scaleY = size.height / maxOf(1, box.imageHeight)
            val left = box.xMin * scaleX
            val top = box.yMin * scaleY
            val width = (box.xMax - box.xMin) * scaleX
            val height = (box.yMax - box.yMin) * scaleY
            drawRect(color = color, topLeft = Offset(left, top), size = Size(width, height), style = Stroke(width = 4f))
            val label = detectionLabelText(box)
            val labelHeight = 28.dp.toPx()
            val labelWidth = maxOf(76.dp.toPx(), label.length * 8.dp.toPx() + 24.dp.toPx())
            val bounds = detectionLabelBounds(box, size.width, size.height, labelWidth, labelHeight)
            drawRoundRect(
                color = color.copy(alpha = 0.88f),
                topLeft = Offset(bounds.left, bounds.top),
                size = Size(bounds.right - bounds.left, bounds.bottom - bounds.top),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(8.dp.toPx(), 8.dp.toPx())
            )
            drawContext.canvas.nativeCanvas.drawText(
                label,
                bounds.left + 10.dp.toPx(),
                bounds.top + 19.dp.toPx(),
                textPaint
            )
        }
    }
}

@Composable
private fun DetectionHistoryScreen(state: AppUiState, viewModel: MDetectViewModel) {
    AppShell("Detection History", state, viewModel) {
        if (state.history.isEmpty()) {
            Text("서버에서 이력 조회 API를 사용할 수 없습니다.")
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.history) { item ->
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(12.dp)) {
                            Text("${item.mode ?: "-"} / ${item.modelVersion ?: "-"}")
                            Text("${item.topClass ?: "-"}  ${item.topConfidence ?: 0f}")
                            Text(item.createdAt ?: "-")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ModelUpdateScreen(state: AppUiState, viewModel: MDetectViewModel) {
    AppShell("Model Update", state, viewModel) {
        InfoCard("Local model", state.modelMetadata.modelVersion)
        InfoCard("Latest server model", state.latestServerModel?.modelVersion ?: "Not checked")
        InfoCard("Downloaded files", state.modelFileState.summary)
        InfoCard("Local model size", "${state.modelFileState.modelBytes} bytes")
        Button(onClick = viewModel::checkLatestModel, modifier = Modifier.fillMaxWidth()) { Text("Check latest model") }
        Spacer(Modifier.height(8.dp))
        Button(onClick = viewModel::downloadLatestModel, modifier = Modifier.fillMaxWidth()) { Text("Download model package") }
    }
}

private fun compactDebug(value: String, maxLength: Int = 90): String {
    if (value.length <= maxLength) return value
    return value.take(maxLength - 3) + "..."
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingsScreen(state: AppUiState, viewModel: MDetectViewModel) {
    var serverUrl by remember(state.settings.serverUrl) { mutableStateOf(state.settings.serverUrl) }
    var detectionMode by remember(state.settings.detectionMode) { mutableStateOf(state.settings.detectionMode) }
    var interval by remember(state.settings.frameIntervalMs) { mutableLongStateOf(state.settings.frameIntervalMs) }
    var confidence by remember(state.settings.confidenceThreshold) { mutableStateOf(state.settings.confidenceThreshold) }
    var iou by remember(state.settings.iouThreshold) { mutableStateOf(state.settings.iouThreshold) }
    var modeExpanded by remember { mutableStateOf(false) }
    var intervalExpanded by remember { mutableStateOf(false) }
    var showLogoutDialog by remember { mutableStateOf(false) }

    if (showLogoutDialog) {
        ConfirmLogoutDialog(
            onDismiss = { showLogoutDialog = false },
            onConfirm = {
                showLogoutDialog = false
                viewModel.logout()
            }
        )
    }

    AppShell("Settings", state, viewModel) {
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { OutlinedTextField(value = serverUrl, onValueChange = { serverUrl = it }, label = { Text("Server URL") }, modifier = Modifier.fillMaxWidth()) }
            item {
                ExposedDropdownMenuBox(expanded = modeExpanded, onExpandedChange = { modeExpanded = !modeExpanded }) {
                    OutlinedTextField(
                        value = detectionMode.name,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Detection Mode") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = modeExpanded) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = modeExpanded, onDismissRequest = { modeExpanded = false }) {
                        DetectionMode.entries.forEach { mode ->
                            DropdownMenuItem(text = { Text(mode.name) }, onClick = { detectionMode = mode; modeExpanded = false })
                        }
                    }
                }
            }
            item {
                ExposedDropdownMenuBox(expanded = intervalExpanded, onExpandedChange = { intervalExpanded = !intervalExpanded }) {
                    OutlinedTextField(
                        value = "${interval / 1000.0}s",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Server Mode Interval") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = intervalExpanded) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(expanded = intervalExpanded, onDismissRequest = { intervalExpanded = false }) {
                        listOf(500L, 1000L, 2000L).forEach { value ->
                            DropdownMenuItem(text = { Text("${value / 1000.0}s") }, onClick = { interval = value; intervalExpanded = false })
                        }
                    }
                }
            }
            item { Text("Confidence Threshold: ${"%.2f".format(confidence)}"); Slider(value = confidence, onValueChange = { confidence = it }, valueRange = 0.05f..0.95f) }
            item { Text("IoU Threshold: ${"%.2f".format(iou)}"); Slider(value = iou, onValueChange = { iou = it }, valueRange = 0.05f..0.95f) }
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        viewModel.saveSettings(AppSettings(serverUrl, detectionMode, interval, confidence, iou, state.settings.username, ""))
                    }) { Text("Save") }
                    Button(onClick = viewModel::testConnection) { Text("Test") }
                    Button(onClick = { viewModel.navigate(AppScreen.LOGIN) }) { Text("Login") }
                }
            }
            item {
                Button(
                    onClick = { showLogoutDialog = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF991B1B), contentColor = Color.White)
                ) { Text("로그아웃") }
            }
        }
    }
}
