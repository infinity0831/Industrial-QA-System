<script setup>
import { ref, computed } from 'vue';
import { Plus, Search, X, CheckSquare, Activity, Edit3, Save, Cpu, Filter, BarChart2, Layers, Zap, TrendingUp, Stethoscope } from 'lucide-vue-next';

// --- 1. 定义工具数据 (分类已调整为 PHM 四层架构，内容还原为详细版) ---
const toolsData = ref({
  // =========================
  // 1. 描述 (Description) - 信号处理与特征提取
  // =========================
  wavelet: {
    id: 'wavelet',
    category: '描述',
    name: 'preprocess_wavelet_denoising',
    description: '【核心组件】小波阈值去噪算法。用于去除传感器信号中的高频噪声，保留故障冲击特征。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "preprocess_wavelet_denoising",
        description: `
【功能描述】
工业信号处理的标准“清洗”工具。
基于小波变换（Wavelet Transform）对非平稳信号进行多尺度分解，通过软/硬阈值处理去除高频噪声（如电磁干扰、环境杂波），同时保留故障引起的冲击特征。

【调用时机】
1. **首选步骤**：当用户输入原始传感器波形数据（Raw Waveform）且未经过处理时。
2. **前置依赖**：必须在“特征提取”（如 TFCAT, FFT）之前调用。只有数据干净了，提取的特征才准确。
3. 适用场景：振动、声发射等包含大量背景噪声的非平稳信号。

【预期效果】
- 显著提高信噪比（SNR）。
- 使后续的频谱分析图谱更加清晰，减少误报。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            data_id: { type: "string", description: "【关键参数】待去噪的数据流ID或文件路径。" },
            wavelet_base: { type: "string", description: "小波基函数。推荐 'db4' 或 'sym8'。", default: "db4" },
            level: { type: "integer", description: "分解层数。通常设为 3-5 层。", default: 3 },
            threshold_rule: { type: "string", description: "阈值规则。可选 'soft' 或 'hard'。", enum: ["soft", "hard"], default: "soft" }
          },
          required: ["data_id"]
        }
      }
    }, null, 2)
  },
  tfcat: {
    id: 'tfcat',
    category: '描述',
    name: 'feature_extraction_tfcat',
    description: '【核心组件】时频特征分析工具。用于从振动信号中提取 RMS、峭度、能量谱等关键故障特征，将波形转化为指标。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "feature_extraction_tfcat",
        description: `
【功能描述】
工业信号分析的“显微镜”。不仅计算单一的统计量，还能进行时频联合分析。
它能提取：
1. **时域特征**：有效值(RMS)、峰值(Peak)、峭度(Kurtosis)、波形因子。
2. **频域特征**：重心频率、均方频率、能量谱密度。
特别适用于非平稳信号（如轴承剥落、齿轮断齿）的特征捕捉。

【调用时机】
1. **承接步骤**：在“数据预处理”（去噪）之后调用。
2. **前置步骤**：在“故障诊断”（如 SVM 分类）之前调用。
3. **场景**：当原始波形数据无法直接判断时，必须先提取特征向量。

【预期输出】
- 返回特征JSON对象（如 {"rms": 5.2, "kurtosis": 4.8}）。
- AI 应关注 **峭度(Kurtosis)**：>3 通常意味着存在早期冲击故障；**RMS**：显著升高意味着故障已发展到中后期。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】待分析的信号数据流ID。" },
            window_size: { type: "integer", description: "分析窗口大小。建议 1024 或 2048。", default: 1024 },
            features: { type: "array", items: { type: "string" }, description: "指定特征列表。支持 'rms', 'peak', 'kurtosis', 'energy_spectrum'。", default: ["rms", "peak", "kurtosis"] }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },
  fft: {
    id: 'fft',
    category: '描述',
    name: 'feature_extraction_fft',
    description: '【核心组件】快速傅里叶变换。旋转机械故障诊断的“听诊器”，用于将时域波形转换为频谱，定位不平衡、不对中等故障频率。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "feature_extraction_fft",
        description: `
【功能描述】
旋转机械故障诊断的“听诊器”。将时域波形信号转换为频域频谱。
【核心能力】
1. **基频分析**：识别转速频率（1X），大幅值通常意味着“动不平衡”。
2. **倍频分析**：识别 2X, 3X 等高次谐波，通常对应“不对中”或“机械松动”。
3. **特征频率匹配**：检测特定的轴承故障频率（BPFO, BPFI）或齿轮啮合频率。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】待分析的振动信号ID。" },
            sampling_rate: { type: "integer", description: "采样率(Hz)。默认为 5120Hz。", default: 5120 },
            window_function: { type: "string", description: "窗函数。推荐 'hanning'。", default: "hanning" },
            top_k_peaks: { type: "integer", description: "仅返回前 K 个峰值。", default: 5 }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },
  // --- 新增算法 1: VMD (变分模态分解) ---
  vmd: {
    id: 'vmd',
    category: '描述',
    name: 'preprocess_vmd_decomposition',
    description: '【进阶组件】变分模态分解。相比EMD，它能有效避免模态混叠，将复杂信号分解为指定数量的带限本征模态函数。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "preprocess_vmd_decomposition",
        description: `
【功能描述】
非平稳信号处理的“现代利器”。基于变分理论的信号分解方法。
相比 EMD，VMD 具有坚实的数学理论基础，能有效解决“模态混叠”和“端点效应”问题。
【核心能力】
1. **自适应分解**：将信号分解为 K 个围绕中心频率的窄带模态 (IMF)。
2. **抗噪性强**：在强噪声背景下仍能提取微弱的冲击成分。
【调用时机】
1. **场景**：当 EMD 效果不佳（出现模态混叠）时，或者需要精细化提取特定频带信号时。
2. **参数敏感**：需要预设分解层数 K，通常结合“中心频率观察”来确定。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】待分解的信号ID。" },
            k_modes: { type: "integer", description: "分解模态数(K)。通常设为 3-6。", default: 4 },
            alpha: { type: "integer", description: "惩罚因子（带宽限制）。通常 2000。", default: 2000 }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },

  // --- 新增算法 2: Envelope (包络分析) ---
  envelope: {
    id: 'envelope',
    category: '描述',
    name: 'feature_extraction_envelope_spectrum',
    description: '【核心组件】包络谱分析（希尔伯特解调）。滚动轴承故障诊断的标准方法，用于解调出高频共振波中的低频故障冲击。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "feature_extraction_envelope_spectrum",
        description: `
【功能描述】
滚动轴承诊断的“显影液”。利用希尔伯特变换（Hilbert Transform）进行包络解调。
【物理机理】
当轴承发生损伤时，旋转会产生周期性的冲击，这些冲击会激起轴承座的高频固有频率（共振）。
包络分析的作用就是去除高频载波，还原出低频的故障冲击频率（BPFO, BPFI, BSFF）。
【调用时机】
1. **首选场景**：怀疑是滚动轴承故障时（点蚀、剥落）。
2. **流程**：带通滤波 -> 希尔伯特变换 -> 取模 -> FFT。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】原始振动信号ID。" },
            band_pass_filter: { type: "array", items: { type: "number" }, description: "共振频带范围 [low, high] (Hz)。", default: [2000, 4000] }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },

  // --- 新增算法 3: Cepstrum (倒频谱) ---
  cepstrum: {
    id: 'cepstrum',
    category: '描述',
    name: 'feature_extraction_cepstrum',
    description: '【进阶组件】倒频谱分析。齿轮箱故障诊断专家，擅长识别频谱中的周期性结构（边频带），分离源信号与传递路径。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "feature_extraction_cepstrum",
        description: `
【功能描述】
齿轮箱诊断的“透镜”。是“频谱的频谱”（Spectrum of Spectrum）。
【核心能力】
1. **边频带检测**：齿轮故障（如断齿、磨损）会在啮合频率周围产生大量边频带，在频谱上很难看清，但在倒频谱上会变成一个明显的单峰（倒频率）。
2. **回波消除**：能有效分离原始信号和传递路径的影响。
【调用时机】
1. **场景**：复杂的齿轮箱、变速箱振动分析。
2. **目标**：寻找周期性的调制成分。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】振动信号ID。" },
            output_type: { type: "string", description: "实倒频谱或复倒频谱。", enum: ["real", "complex"], default: "real" }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },

  // --- 新增算法 4: STFT (短时傅里叶变换) ---
  stft: {
    id: 'stft',
    category: '描述',
    name: 'feature_extraction_stft',
    description: '【基础组件】短时傅里叶变换。生成时频图（Spectrogram），展示频率随时间的变化，常作为CNN深度学习模型的输入图。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "feature_extraction_stft",
        description: `
【功能描述】
最直观的时频分析工具。通过加窗滑动的 FFT，描绘出频率随时间变化的二维热力图。
【核心能力】
1. **瞬态捕捉**：能看到设备启动、停止过程中的频率爬升（Run-up/Run-down）。
2. **图像化特征**：生成的声谱图（Spectrogram）是卷积神经网络（CNN）最理想的输入数据。
【调用时机】
1. **场景**：变转速工况分析，或准备进行深度学习训练时。
2. **权衡**：受海森堡测不准原理限制，需在时间分辨率和频率分辨率间做权衡（通过窗长调整）。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】振动信号ID。" },
            window_size: { type: "integer", description: "窗长。越小时间分辨率越高，频率分辨率越低。", default: 256 },
            overlap: { type: "integer", description: "重叠点数。", default: 128 }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },
  sk: {
    id: 'sk',
    category: '描述',
    name: 'feature_extraction_spectral_kurtosis',
    description: '【核心组件】谱峭度分析。强噪声背景下“透视”故障的利器，用于定位共振频带，发现早期微弱冲击信号。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "feature_extraction_spectral_kurtosis",
        description: `
【功能描述】
强噪声背景下的“透视眼”。度量信号在不同频率位置的“非高斯性”。
【核心能力】
1. **最佳频带定位**：生成谱峭度图，找出峭度最大的中心频率和带宽。
2. **抗噪能力强**：即使信噪比极低，也能发现异常频带。
3. **早期故障敏感**：对微弱冲击非常敏感。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            signal_id: { type: "string", description: "【关键参数】待分析的信号ID。" },
            sampling_rate: { type: "integer", description: "采样率(Hz)。", default: 5120 }
          },
          required: ["signal_id"]
        }
      }
    }, null, 2)
  },
  ica: {
    id: 'ica',
    category: '描述',
    name: 'detection_ica',
    description: '【核心组件】独立成分分析。用于“盲源分离”，将混合在一起的多种故障信号或噪声分离成独立的源信号。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "detection_ica",
        description: `
【功能描述】
工业信号处理的“解构师”。解决“鸡尾酒会问题”（盲源分离）。
将混合信号还原为相互独立的源信号（如：分离轴承故障声和环境噪声）。
【调用时机】
1. **场景**：复合故障诊断，或多通道传感器数据高度耦合。
2. **对比**：PCA 用于降维去相关，ICA 用于分离独立源。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            data_source: { type: "string", description: "【关键参数】多通道观测信号ID。" },
            n_components: { type: "integer", description: "独立成分数量。" }
          },
          required: ["data_source"]
        }
      }
    }, null, 2)
  },

  // =========================
  // 2. 健康评估 (Health Assessment) - 异常检测
  // =========================
  iso_forest: {
    id: 'iso_forest',
    category: '健康评估',
    name: 'detection_isolation_forest',
    description: '【核心组件】孤立森林。高效的无监督异常检测算法，专门用于在海量或高维数据中快速筛选“离群点”。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "detection_isolation_forest",
        description: `
【功能描述】
大数据时代的“异常捕手”。不建立正常模型，直接利用异常点“少且不同”的特点将其孤立。
【核心能力】
1. **无监督学习**：无需历史标签，冷启动可用。
2. **高效处理**：线性时间复杂度，适合海量数据。
3. **脏数据适应性**：对不符合高斯分布的数据适应性强。
【调用时机】
1. **场景**：冷启动监控，或数据清洗阶段剔除明显离群值。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            data_source: { type: "string", description: "【关键参数】待检测的数据集ID。" },
            contamination: { type: ["string", "number"], description: "预计异常比例。默认 'auto'。", default: "auto" }
          },
          required: ["data_source"]
        }
      }
    }, null, 2)
  },
  kpca: {
    id: 'kpca',
    category: '健康评估',
    name: 'detection_kpca',
    description: '【核心组件】KPCA非线性检测。通过核技巧处理多变量耦合数据，同时监测 SPE 和 T² 统计量，精准发现异常。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "detection_kpca",
        description: `
【功能描述】
非线性过程监测的“金标准”。通过核函数映射到高维空间，处理“非线性耦合”关系。
【核心能力】
1. **双重监测**：计算 SPE (残差空间变化) 和 T² (主元空间变化)。
2. **非线性解耦**：处理复杂的变量耦合。
【调用时机】
1. **场景**：化工、连铸等复杂非线性过程。
2. **预期输出**：SPE/T² 曲线及变量贡献率排序。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            data_source: { type: "string", description: "【关键参数】多变量过程数据ID。" },
            kernel: { type: "string", description: "核函数类型。", default: "rbf" },
            confidence_level: { type: "number", description: "控制限置信度。", default: 0.99 }
          },
          required: ["data_source"]
        }
      }
    }, null, 2)
  },
  pca: {
    id: 'pca',
    category: '健康评估',
    name: 'detection_pca',
    description: '【核心组件】PCA线性检测。经典的多元统计过程控制(MSPC)工具，用于稳态、线性系统的异常监测与降维。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "detection_pca",
        description: `
【功能描述】
工业过程监测的“基石”。处理“数据冗余”和“线性相关”，计算速度快。
【核心能力】
1. **降维去噪**：保留主要变化趋势。
2. **异常监测**：T² (工况偏离) 和 SPE (相关性破坏)。
【调用时机】
1. **场景**：平稳运行且变量间呈线性关系的系统。
2. **优势**：开销低，适合实时监测。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            data_source: { type: "string", description: "【关键参数】多变量过程数据ID。" },
            n_components: { type: "number", description: "保留比例(0-1)或个数。", default: 0.95 }
          },
          required: ["data_source"]
        }
      }
    }, null, 2)
  },
  ahp: {
    id: 'ahp',
    category: '健康评估',
    name: 'assessment_ahp_weighting',
    description: '【核心组件】层次分析法。一种定性与定量结合的决策工具，用于确定多维特征的权重，构建设备综合健康度(HI)。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "assessment_ahp_weighting",
        description: `
【功能描述】
将专家经验转化为数学权重的“翻译官”。
在构建设备健康指标（Health Index）时，面对振动、温度、电流等多个维度的特征，AHP 通过两两比较矩阵（Pairwise Comparison Matrix），计算出每个特征的相对权重。
它能将主观的专家判断逻辑化、数学化，并进行一致性检验。

【核心能力】
1. **多源融合权重计算**：解决“振动指标和温度指标哪个更重要？”的问题。
2. **一致性检验 (CR Check)**：自动检测专家的判断逻辑是否自相矛盾（如：A>B, B>C，但 A<C？这是不通过的）。
3. **综合健康评分**：基于计算出的权重，对多维特征进行加权求和，输出 0-100 的健康分。

【调用时机】
1. **场景**：需要融合多传感器数据构建“设备健康画像”时。
2. **前置**：通常在提取了多个特征（RMS, 峰值, 温度）之后，但在这写特征进入最终评估模型之前。
3. **对比**：PCA 是基于数据方差定权重（客观），AHP 是基于故障机理定权重（主观专家经验）。两者常结合使用。

【预期输出】
- **特征权重向量**：(e.g., 振动: 0.6, 温度: 0.3, 噪声: 0.1)。
- **一致性比率 (CR)**：若 CR < 0.1，说明判断矩阵有效；否则需调整矩阵。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            criteria: {
              type: "array",
              items: { type: "string" },
              description: "【关键参数】参与评估的特征或指标名称列表。例如：['RMS', 'Kurtosis', 'Temperature']。"
            },
            comparison_matrix: {
              type: "array",
              items: {
                type: "array",
                items: { type: "number" }
              },
              description: "【核心参数】专家判断矩阵（N x N）。\n元素 a[i][j] 表示指标 i 相对于指标 j 的重要程度（1=同等重要, 3=稍微重要, 5=明显重要, 9=极端重要）。\n矩阵必须是互反的（a[j][i] = 1/a[i][j]）。"
            }
          },
          required: ["criteria", "comparison_matrix"]
        }
      }
    }, null, 2)
  },

  // =========================
  // 3. 诊断 (Diagnosis) - 故障分类与归因
  // =========================
  svm: {
    id: 'svm',
    category: '诊断',
    name: 'diagnosis_svm_classifier',
    description: '【核心组件】支持向量机分类器。小样本故障诊断之王，用于基于特征向量对故障类型进行精准识别。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_svm_classifier",
        description: `
【功能描述】
小样本分类的“定海神针”。在特征空间寻找最优超平面。
【核心能力】
1. **精准分类**：输入特征向量，输出故障类别。
2. **鲁棒性**：对小样本场景效果优于深度学习。
【调用时机】
1. **前置**：必须先提取特征（如 RMS, 峭度）。
2. **场景**：已知故障类型标签，需进行分类。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            feature_vector: { type: "array", items: { type: "number" }, description: "【关键参数】输入特征向量。" },
            kernel: { type: "string", description: "核函数类型。", default: "rbf" }
          },
          required: ["feature_vector"]
        }
      }
    }, null, 2)
  },
  // --- 新增算法: LSTM (长短期记忆网络) ---
  lstm: {
    id: 'lstm',
    category: '诊断',
    name: 'diagnosis_lstm_classifier',
    description: '【核心组件】长短期记忆网络。擅长处理时间序列数据的深度学习模型，通过门控机制捕捉故障演变的时间依赖性。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_lstm_classifier",
        description: `
【功能描述】
时间序列分类的“记忆大师”。
不同于 CNN 关注局部特征，LSTM 擅长记忆长序列中的历史信息，判断当前状态是否异常。

【核心能力】
1. **时序建模**：能捕捉“故障是如何一步步演变出来的”（上下文依赖），而不仅仅看当前的瞬间数值。
2. **解决长依赖**：通过“遗忘门、输入门、输出门”机制，有效利用历史数据，避免梯度消失。

【调用时机】
1. **场景**：当单一时刻的特征（如 RMS）不足以区分故障，需要结合过去几秒甚至几分钟的变化趋势来进行分类时。
2. **输入**：通常是多维时间序列矩阵（Time-Steps x Features）。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            sequence_id: { type: "string", description: "【关键参数】输入的时间序列数据ID。" },
            hidden_units: { type: "integer", description: "隐藏层单元数。", default: 64 },
            layers: { type: "integer", description: "堆叠层数。", default: 2 }
          },
          required: ["sequence_id"]
        }
      }
    }, null, 2)
  },
  // --- 新增算法: Transfer Learning (迁移学习) ---
  transfer_learning: {
    id: 'transfer_learning',
    category: '诊断',
    name: 'diagnosis_transfer_learning',
    description: '【进阶组件】迁移学习。解决“新设备无故障样本”难题，将旧设备的故障诊断模型知识迁移到新工况或新设备上。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_transfer_learning",
        description: `
【功能描述】
工业AI的“举一反三”能力。
解决不同工况（如转速、负载变化）或不同设备间的“域偏移”问题。

【核心能力】
1. **域自适应**：缩小源域（有标签）和目标域（无标签）的特征分布差异。
2. **小样本冷启动**：在新机器刚上线、几乎没有故障数据时，直接复用类似机器的诊断能力。

【调用时机】
1. **场景**：同一型号电机，从A厂（数据多）迁移到B厂（数据少）；或同一设备从变频工况A迁移到工况B。
2. **前置**：需要一个在相似设备上训练好的“源模型”。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            source_model_id: { type: "string", description: "【关键参数】源域预训练模型ID。" },
            target_data: { type: "string", description: "【关键参数】目标域数据（少量或无标签）。" },
            method: { type: "string", description: "迁移方法。", enum: ["MMD", "Adversarial", "Fine-tune"], default: "Fine-tune" }
          },
          required: ["source_model_id", "target_data"]
        }
      }
    }, null, 2)
  },

  // --- 新增算法: Decision Tree (决策树) ---
  decision_tree: {
    id: 'decision_tree',
    category: '诊断',
    name: 'diagnosis_decision_tree',
    description: '【基础组件】决策树。完全“白盒”的分类算法，能够生成类似“若 RMS>5 且 Temp>60 则 轴承故障”的直观规则。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_decision_tree",
        description: `
【功能描述】
最透明的“规则生成器”。通过树状结构逐步对特征进行分裂判断。

【核心能力】
1. **规则提取**：模型训练完后，可以直接转化为人工可读的 IF-THEN 规则，方便写入 PLC 或 SCADA 系统。
2. **白盒解释**：每一步判断都有明确依据，无黑箱操作。

【调用时机】
1. **场景**：对模型“可解释性”要求极高，或需要将 AI 逻辑硬编码到嵌入式芯片中时。
2. **对比**：精度通常低于随机森林/XGBoost，但解释性最强。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            feature_vector: { type: "array", items: { type: "number" }, description: "【关键参数】输入特征向量。" },
            criterion: { type: "string", description: "分裂准则。", enum: ["gini", "entropy"], default: "gini" },
            max_depth: { type: "integer", description: "树的最大深度。", default: 5 }
          },
          required: ["feature_vector"]
        }
      }
    }, null, 2)
  },
  random_forest: {
    id: 'random_forest',
    category: '诊断',
    name: 'diagnosis_random_forest',
    description: '【核心组件】随机森林分类器。基于集成学习的“多面手”，不仅能精准诊断故障类型，还能给出特征重要性解释。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_random_forest",
        description: `
【功能描述】
工业故障诊断的“多面手”。优势在于**可解释性**：指出哪些特征导致了故障判定。
【核心能力】
1. **高鲁棒性**：对噪声和缺失值有强容忍度。
2. **特征重要性**：计算每个特征对分类的贡献度。
【预期输出】
故障类别、置信度、以及关键特征排序（如 "主要依据：峭度"）。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            feature_vector: { type: "array", items: { type: "number" }, description: "【关键参数】输入特征向量。" },
            feature_names: { type: "array", items: { type: "string" }, description: "特征名称列表，用于解释性报告。" }
          },
          required: ["feature_vector"]
        }
      }
    }, null, 2)
  },
  // --- 新增诊断算法 1: XGBoost ---
  xgboost: {
    id: 'xgboost',
    category: '诊断',
    name: 'diagnosis_xgboost_classifier',
    description: '【核心组件】XGBoost分类器。梯度提升树算法的巅峰之作，在结构化数据（特征表）的故障分类任务中，通常拥有最高的准确率。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_xgboost_classifier",
        description: `
【功能描述】
结构化数据竞赛的“常胜将军”。基于梯度提升决策树（GBDT）的优化实现。
【核心能力】
1. **极致精度**：通过迭代优化残差，对复杂边界的拟合能力极强。
2. **稀疏处理**：能自动处理特征中的缺失值（如传感器偶尔丢包）。
【调用时机】
1. **场景**：当随机森林精度遇到瓶颈，且计算资源允许时。
2. **对比**：SVM 适合小样本；XGBoost 适合中大样本且特征维度较高的场景。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            feature_vector: { type: "array", items: { type: "number" }, description: "【关键参数】输入特征向量。" },
            learning_rate: { type: "number", description: "学习率(eta)。防止过拟合。", default: 0.1 },
            max_depth: { type: "integer", description: "树的最大深度。", default: 6 }
          },
          required: ["feature_vector"]
        }
      }
    }, null, 2)
  },

  // --- 新增诊断算法 2: CNN (深度学习) ---
  cnn: {
    id: 'cnn',
    category: '诊断',
    name: 'diagnosis_cnn_classifier',
    description: '【核心组件】卷积神经网络。深度学习代表，擅长“端到端”诊断，能直接从原始波形或时频图谱中自动提取特征并分类。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_cnn_classifier",
        description: `
【功能描述】
工业视觉与信号的“大脑”。无需人工设计特征（RMS/峭度等），直接从原始数据中学习故障模式。
【核心能力】
1. **自动特征提取**：通过卷积层捕捉局部相关性（如周期性冲击）。
2. **处理高维数据**：直接输入二维的时频图（STFT图）或一维原始波形。
【调用时机】
1. **场景**：数据量巨大，且人工提取的特征无法区分故障时。
2. **输入**：通常是 TFCAT 生成的频谱图矩阵，或原始振动序列。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            input_tensor: { type: "string", description: "【关键参数】输入数据的张量ID（图像或序列）。" },
            architecture: { type: "string", description: "网络架构模型。", enum: ["ResNet18", "1D-CNN", "LeNet"], default: "1D-CNN" }
          },
          required: ["input_tensor"]
        }
      }
    }, null, 2)
  },

  // --- 新增诊断算法 3: k-NN (基础基线) ---
  knn: {
    id: 'knn',
    category: '诊断',
    name: 'diagnosis_knn_classifier',
    description: '【核心组件】K近邻算法。基于实例的惰性学习算法，“近朱者赤”，通过寻找最相似的历史案例来判断当前故障类型。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "diagnosis_knn_classifier",
        description: `
【功能描述】
最直观的“类比推理”算法。不建立通用模型，而是实时在历史数据库中搜索最相似的 K 个样本进行投票。
【核心能力】
1. **可解释性强**：可以直接展示“与本次故障最像的 3 个历史案例”。
2. **无训练过程**：即插即用，适合样本库动态更新的场景。
【调用时机】
1. **场景**：作为故障诊断的 Baseline（基准线），或用于检索相似案例。
2. **前置**：必须进行特征归一化（Normalization），否则距离计算会失效。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            feature_vector: { type: "array", items: { type: "number" }, description: "【关键参数】输入特征向量。" },
            n_neighbors: { type: "integer", description: "邻居数量(K)。", default: 5 },
            metric: { type: "string", description: "距离度量方式。", default: "euclidean" }
          },
          required: ["feature_vector"]
        }
      }
    }, null, 2)
  },
  krt: {
    id: 'krt',
    category: '诊断',
    name: 'search_knowledge_base',
    description: '【核心组件】工业运维知识图谱检索引擎。用于故障归因与解决方案匹配。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "search_knowledge_base",
        description: `
【功能描述】
故障诊断流程中“承上启下”的核心工具。连接“数据世界”与“物理世界”。
用于在 Neo4j 图谱中检索实体、故障模式及维修策略。
【调用时机】
**必须**在算法分析出具体的“异常特征”或“关键变量”之后调用。
【预期返回】
关联设备节点、故障原因、维修建议。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            query: { type: "string", description: "【关键参数】检索关键词（变量名、故障现象等）。" },
            limit: { type: "integer", default: 3 }
          },
          required: ["query"]
        }
      }
    }, null, 2)
  },

  // =========================
  // 4. 预测 (Prediction) - 状态估计
  // =========================
  kalman: {
    id: 'kalman',
    category: '预测',
    name: 'preprocess_kalman_filter',
    description: '【核心组件】卡尔曼滤波算法。用于平滑温度、压力、流量等过程数据的测量噪声，还原真实状态。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "preprocess_kalman_filter",
        description: `
【功能描述】
基于最小均方误差准则的最优估计算法。融合“系统预测”和“传感器测量”，动态估计最优状态。
【调用时机】
1. **适用数据**：温度、压力、流量等连续变化的平稳过程量。
2. **对比**：冲击信号用小波；平稳波动用卡尔曼。
3. **用途**：趋势预测或 RUL 预测的前置步骤。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            data_id: { type: "string", description: "【关键参数】待处理的过程量数据ID。" },
            process_noise_cov: { type: "number", default: 0.01 },
            measurement_noise_cov: { type: "number", default: 0.1 }
          },
          required: ["data_id"]
        }
      }
    }, null, 2)
  },
  // --- 新增算法 1: ARIMA (时间序列预测) ---
  arima: {
    id: 'arima',
    category: '预测',
    name: 'prediction_arima',
    description: '【基础组件】自回归积分滑动平均模型。经典的统计学时间序列预测工具，适用于短期、线性的趋势外推。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "prediction_arima",
        description: `
【功能描述】
统计学预测的“基石”。不依赖物理模型，仅从历史数据的自相关性中学习规律。
适用于预测具备一定惯性趋势的过程量（如温度缓慢升高、振动幅值逐渐增大）。

【核心能力】
1. **差分平稳化**：通过差分（I）消除不平稳趋势。
2. **短期预测**：对未来 3-5 个时间步长的预测精度较高。

【调用时机】
1. **场景**：单变量时间序列预测，且数据量较小，不适合跑深度学习时。
2. **局限**：难以捕捉非线性突变。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            time_series_id: { type: "string", description: "【关键参数】历史时间序列数据ID。" },
            order: { type: "array", items: { type: "integer" }, description: "模型阶数 (p, d, q)。", default: [1, 1, 1] },
            forecast_steps: { type: "integer", description: "向后预测的步数。", default: 5 }
          },
          required: ["time_series_id"]
        }
      }
    }, null, 2)
  },

  // --- 新增算法 2: SVR (支持向量回归) ---
  svr: {
    id: 'svr',
    category: '预测',
    name: 'prediction_svr',
    description: '【进阶组件】支持向量回归。SVM算法的回归版本，利用核函数将非线性趋势映射到高维空间进行线性回归，鲁棒性强。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "prediction_svr",
        description: `
【功能描述】
小样本趋势预测的“利器”。
与 SVM 分类类似，SVR 寻找一个“回归管道”，让尽可能多的数据点落在管道内。

【核心能力】
1. **泛化能力强**：通过最大化间隔，避免过拟合，对噪声数据有很好的容忍度。
2. **非线性映射**：通过 RBF 核函数处理复杂的非线性退化趋势。

【调用时机】
1. **场景**：预测设备的性能退化指标（如健康度 HI 下降趋势）。
2. **对比**：比线性回归更强，比神经网络更稳定（在小样本下）。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            feature_matrix: { type: "string", description: "【关键参数】历史特征矩阵ID。" },
            kernel: { type: "string", description: "核函数。", enum: ["rbf", "linear", "poly"], default: "rbf" },
            C: { type: "number", description: "惩罚系数。", default: 1.0 }
          },
          required: ["feature_matrix"]
        }
      }
    }, null, 2)
  },

  // --- 新增算法 3: Particle Filter (粒子滤波) ---
  particle_filter: {
    id: 'particle_filter',
    category: '预测',
    name: 'prediction_particle_filter',
    description: '【高级组件】粒子滤波。基于贝叶斯方法的非线性状态估计算法，常用于结合物理失效模型进行剩余寿命(RUL)预测。',
    schema: JSON.stringify({
      type: "function",
      function: {
        name: "prediction_particle_filter",
        description: `
【功能描述】
RUL 预测的“金标准”。
用大量随机样本（粒子）来模拟系统的概率分布。不仅能给出预测值，还能给出预测的**置信区间**（不确定性）。

【核心能力】
1. **处理非线性/非高斯**：比卡尔曼滤波更强大，适用于复杂的物理退化过程（如疲劳裂纹扩展）。
2. **概率预测**：输出形式为“剩余寿命还有 100 小时的概率是 80%”。

【调用时机】
1. **场景**：结合物理退化模型（如 Paris 公式）预测关键部件的剩余寿命。
2. **代价**：计算量大，粒子数越多越慢。
        `.trim(),
        parameters: {
          type: "object",
          properties: {
            observation_data: { type: "string", description: "【关键参数】观测数据流ID。" },
            num_particles: { type: "integer", description: "粒子数量。", default: 1000 },
            model_type: { type: "string", description: "物理退化模型类型。", default: "exponential_degradation" }
          },
          required: ["observation_data"]
        }
      }
    }, null, 2)
  },
});

// --- 2. 核心逻辑：按分类分组 ---
const categoryOrder = ['描述', '健康评估', '诊断', '预测'];

const groupedTools = computed(() => {
  const groups = {};
  categoryOrder.forEach(c => groups[c] = []);
  
  Object.values(toolsData.value).forEach(tool => {
    if (groups[tool.category]) {
      groups[tool.category].push(tool);
    } else {
      if (!groups['其他']) groups['其他'] = [];
      groups['其他'].push(tool);
    }
  });
  return groups;
});

// 编辑逻辑
const isEditModalOpen = ref(false);
const currentEditContent = ref('');
const currentToolId = ref('');

const openEditModal = (toolId) => {
  currentToolId.value = toolId;
  currentEditContent.value = toolsData.value[toolId].schema;
  isEditModalOpen.value = true;
};

const saveTool = () => {
  try {
    const parsed = JSON.parse(currentEditContent.value);
    toolsData.value[currentToolId.value].schema = JSON.stringify(parsed, null, 2);
    isEditModalOpen.value = false;
  } catch (e) { alert("JSON Error: " + e.message); }
};

const handleCreateTool = () => {
  const newId = 'tool_' + Date.now();
  toolsData.value[newId] = { 
    id: newId, 
    category: '描述', 
    name: 'new_tool', 
    description: '新工具...', 
    schema: '{}' 
  };
};

const deleteTool = (id) => { delete toolsData.value[id]; };
</script>

<template>
  <div class="tools-layout">
    <div class="toolbar">
      <div class="page-title">
        <Cpu size="24" class="title-icon"/> 算法工具库
      </div>
      <div class="tool-actions">
        <button class="t-btn" @click="handleCreateTool"><Plus size="16"/> 新建工具</button>
        <button class="t-btn search"><Search size="16"/> 搜索</button>
      </div>
    </div>

    <div class="tools-content">
      <div v-for="(categoryName, index) in Object.keys(groupedTools)" :key="index" class="category-row">
        
        <div v-if="groupedTools[categoryName].length > 0" class="row-header">
          <div class="header-left">
            <Activity v-if="categoryName === '描述'" size="20" class="cat-icon desc-icon"/>
            <BarChart2 v-else-if="categoryName === '健康评估'" size="20" class="cat-icon health-icon"/>
            <Stethoscope v-else-if="categoryName === '诊断'" size="20" class="cat-icon diag-icon"/>
            <TrendingUp v-else-if="categoryName === '预测'" size="20" class="cat-icon pred-icon"/>
            <Layers v-else size="20" class="cat-icon"/>
            
            <span class="category-title">{{ categoryName }}</span>
            <span class="category-count">{{ groupedTools[categoryName].length }}</span>
          </div>
          <div class="header-line"></div>
        </div>

        <div v-if="groupedTools[categoryName].length > 0" class="cards-row">
          
          <div v-for="tool in groupedTools[categoryName]" :key="tool.id" class="tool-card">
            <button class="card-edit-btn" @click="openEditModal(tool.id)"><Edit3 size="14" /></button>
            <button class="card-delete-btn" @click="deleteTool(tool.id)"><X size="14" /></button>

            <div class="tool-icon-box" :class="{
              'desc-bg': tool.category === '描述',
              'health-bg': tool.category === '健康评估',
              'diag-bg': tool.category === '诊断',
              'pred-bg': tool.category === '预测'
            }">
              <Activity v-if="tool.category === '描述'" size="32" />
              <BarChart2 v-else-if="tool.category === '健康评估'" size="32" />
              <Stethoscope v-else-if="tool.category === '诊断'" size="32" />
              <TrendingUp v-else-if="tool.category === '预测'" size="32" />
              <Layers v-else size="32" />
            </div>

            <div class="tool-info">
              <div class="tool-name">{{ tool.name }}</div>
              <div class="tool-desc">{{ tool.description }}</div>
            </div>
          </div>

          <div class="tool-card add-card" @click="handleCreateTool">
            <div class="add-icon-circle">
              <Plus size="24" />
            </div>
            <div class="add-text">新建{{ categoryName }}算法</div>
          </div>

        </div>
      </div>
    </div>

    <div v-if="isEditModalOpen" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header"><span>编辑工具定义</span><button class="close-btn" @click="isEditModalOpen=false"><X size="20"/></button></div>
        <div class="modal-body"><textarea v-model="currentEditContent" class="code-editor" spellcheck="false"></textarea></div>
        <div class="modal-footer"><button class="save-btn" @click="saveTool"><Save size="16"/> 保存生效</button></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* --- 布局容器：改为浅色背景 --- */
.tools-layout { 
  padding: 30px 40px; 
  height: 100%; 
  background-color: #f8fafc; /* 关键修改：深色变浅灰 */
  overflow-y: auto; 
  display: flex; 
  flex-direction: column; 
}

/* --- 顶部工具栏 --- */
.toolbar { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 30px; 
  flex-shrink: 0; 
}

.page-title { 
  font-size: 20px; 
  font-weight: bold; 
  color: #1e293b; /* 关键修改：白色变深黑 */
  display: flex; 
  align-items: center; 
  gap: 10px; 
}

.title-icon { 
  color: #3b82f6; 
}

.tool-actions { 
  display: flex; 
  gap: 15px; 
}

/* --- 按钮：白底浅框 --- */
.t-btn { 
  background-color: #ffffff; /* 关键修改 */
  color: #334155;          /* 关键修改 */
  border: 1px solid #cbd5e1; 
  padding: 8px 16px; 
  border-radius: 6px; 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  cursor: pointer; 
  transition: all 0.2s; 
  font-size: 13px; 
  box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
}

.t-btn:hover { 
  border-color: #3b82f6; 
  color: #3b82f6; 
}

/* --- 内容区域 --- */
.tools-content { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  gap: 40px; 
}

/* --- 分类行样式 --- */
.category-row { 
  display: flex; 
  flex-direction: column; 
  gap: 15px; 
}

.row-header { 
  display: flex; 
  align-items: center; 
  gap: 15px; 
}

.header-left { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  flex-shrink: 0; 
}

.category-title { 
  color: #1e293b; /* 关键修改：标题变黑 */
  font-weight: bold; 
  font-size: 16px; 
}

.category-count { 
  background-color: #e2e8f0; /* 关键修改：背景变浅 */
  color: #64748b;          /* 关键修改 */
  font-size: 11px; 
  padding: 2px 8px; 
  border-radius: 10px; 
}

.header-line { 
  flex: 1; 
  height: 1px; 
  background: linear-gradient(to right, #cbd5e1, transparent); /* 关键修改：线条变浅 */
}

/* --- 分类图标颜色 (保持原色或微调) --- */
.cat-icon { opacity: 0.9; }
.desc-icon { color: #0ea5e9; }   
.health-icon { color: #eab308; } 
.diag-icon { color: #9333ea; }   
.pred-icon { color: #10b981; }   

/* --- 卡片样式：白底 + 浅蓝框 --- */
.cards-row { 
  display: flex; 
  flex-wrap: wrap; 
  gap: 20px; 
}

.tool-card { 
  width: 220px; 
  height: 160px; 
  background-color: #ffffff; /* 关键修改：深色变纯白 */
  border: 1px solid #bfdbfe; /* 关键修改：边框变浅蓝 */
  border-radius: 10px; 
  padding: 15px; 
  display: flex; 
  flex-direction: column; 
  position: relative; 
  transition: all 0.2s; 
  box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
}

.tool-card:hover { 
  transform: translateY(-3px); 
  border-color: #3b82f6; 
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); 
}

/* 卡片右上角按钮 */
.card-edit-btn, .card-delete-btn { 
  position: absolute; 
  top: 8px; 
  width: 24px; 
  height: 24px; 
  background: rgba(255, 255, 255, 0.9); /* 关键修改 */
  border: 1px solid #cbd5e1; 
  border-radius: 4px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  cursor: pointer; 
  opacity: 0; 
  transition: all 0.2s; 
  color: #64748b; 
}
.card-edit-btn { right: 8px; }
.card-delete-btn { left: 8px; }

.tool-card:hover .card-edit-btn, .tool-card:hover .card-delete-btn { 
  opacity: 1; 
}

.card-edit-btn:hover { 
  background: #3b82f6; 
  border-color: #3b82f6; 
  color: white; 
}

.card-delete-btn:hover { 
  background: #ef4444; 
  border-color: #ef4444; 
  color: white; 
}

/* 图标盒子背景色调整为浅色系 */
.tool-icon-box { 
  width: 40px; 
  height: 40px; 
  border-radius: 8px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  margin-bottom: 12px; 
}
.desc-bg { background-color: #e0f2fe; color: #0ea5e9; }
.health-bg { background-color: #fef9c3; color: #eab308; }
.diag-bg { background-color: #f3e8ff; color: #9333ea; }
.pred-bg { background-color: #d1fae5; color: #10b981; }

/* 卡片文字 */
.tool-info { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  min-height: 0; 
}

.tool-name { 
  color: #1e293b; /* 关键修改：白色变深黑 */
  font-size: 13px; 
  font-weight: bold; 
  margin-bottom: 5px; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis; 
}

.tool-desc { 
  color: #64748b; /* 关键修改：灰色变深灰 */
  font-size: 12px; 
  line-height: 1.4; 
  overflow: hidden; 
  display: -webkit-box; 
  -webkit-line-clamp: 3; 
  -webkit-box-orient: vertical; 
}

/* --- 弹窗样式 --- */
.modal-overlay { 
  position: fixed; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%; 
  background-color: rgba(0, 0, 0, 0.5); /* 遮罩变浅 */
  z-index: 1000; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  backdrop-filter: blur(2px); 
}

/* --- 新增：虚线添加卡片样式 --- */
.add-card {
  border: 2px dashed #cbd5e1; /* 灰色虚线边框 */
  background-color: #f8fafc;  /* 极浅灰背景，区别于纯白卡片 */
  justify-content: center;    /* 内容垂直居中 */
  align-items: center;        /* 内容水平居中 */
  cursor: pointer;
  box-shadow: none;           /* 去除默认阴影 */
  gap: 10px;                  /* 图标和文字间距 */
}

.add-card:hover {
  border-color: #3b82f6;      /* 悬停变蓝 */
  background-color: #eff6ff;  /* 悬停变浅蓝背景 */
  transform: translateY(-3px);
}

.add-icon-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: #e2e8f0;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.add-card:hover .add-icon-circle {
  background-color: #3b82f6;
  color: white;
}

.add-text {
  font-size: 13px;
  font-weight: bold;
  color: #64748b;
  transition: color 0.2s;
}

.add-card:hover .add-text {
  color: #3b82f6;
}

.modal-content { 
  background-color: #ffffff; /* 关键修改：弹窗白底 */
  width: 600px; 
  max-width: 90vw; 
  border-radius: 12px; 
  border: 1px solid #cbd5e1; 
  display: flex; 
  flex-direction: column; 
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); 
}

.modal-header { 
  padding: 15px 20px; 
  border-bottom: 1px solid #e2e8f0; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  font-weight: bold; 
  color: #1e293b; 
}

.close-btn { 
  background: transparent; 
  border: none; 
  color: #94a3b8; 
  cursor: pointer; 
}
.close-btn:hover { color: #ef4444; }

.modal-body { 
  padding: 0; 
  height: 500px; 
  display: flex; 
}

.code-editor { 
  flex: 1; 
  width: 100%; 
  background-color: #f8fafc; /* 编辑器背景 */
  color: #334155;          /* 编辑器文字 */
  border: none; 
  padding: 20px; 
  font-family: 'Consolas', 'Monaco', monospace; 
  font-size: 13px; 
  line-height: 1.5; 
  resize: none; 
  outline: none; 
  white-space: pre; 
}

.modal-footer { 
  padding: 15px 20px; 
  border-top: 1px solid #e2e8f0; 
  display: flex; 
  justify-content: flex-end; 
}

.save-btn { 
  background-color: #10b981; 
  color: white; 
  border: none; 
  padding: 8px 16px; 
  border-radius: 6px; 
  cursor: pointer; 
  display: flex; 
  align-items: center; 
  gap: 6px; 
  font-weight: bold; 
}

.save-btn:hover { background-color: #059669; }
</style>
