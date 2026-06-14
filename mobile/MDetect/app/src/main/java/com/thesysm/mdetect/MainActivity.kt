package com.thesysm.mdetect

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.thesysm.mdetect.ui.MDetectApp
import com.thesysm.mdetect.ui.theme.MDetectTheme

class MainActivity : ComponentActivity() {
    private val viewModel: MDetectViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MDetectTheme {
                MDetectApp(viewModel = viewModel)
            }
        }
    }
}
