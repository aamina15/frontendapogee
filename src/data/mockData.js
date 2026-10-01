// Central domain data and presets for APOGEE

export const MISSION_PROFILES = [
  {
    id: "ml-cv",
    title: "Python → ML Engineer",
    role: "Machine Learning Engineer",
    track: "CV Track",
    spec: "Specialization: Deep Learning for Computer Vision",
    icon: "alt_route",
    prompt: "I want to become an ML Engineer specializing in computer vision. I know Python and basic mathematics. I can commit 10 hours per week and want to be job-ready in 6 months.",
    baselines: [
      { name: "Python", level: "Intermediate", score: 65, color: "tertiary" },
      { name: "Mathematics", level: "Foundational", score: 35, color: "secondary" }
    ],
    commitment: 10,
    horizon: 6,
    sprints: 24,
    format: "Video + Code",
    language: "English",
    budgetType: "Free only",
    budgetCap: 0,
    bottleneck: "Statistics & PyTorch Tensor Ops — Needed to unlock computer vision model architectures.",
    marketPulse: {
      sampleSize: 2840,
      updatedDate: "Today (Live Feed)",
      demandTrend: "+18.4% Q/Q",
      avgSalary: "$145,000 - $185,000 / yr",
      topSkills: [
        { name: "PyTorch & Tensor Ops", frequency: 92, modelWeight: 0.85, marketWeight: 0.94 },
        { name: "Computer Vision & CNNs", frequency: 86, modelWeight: 0.80, marketWeight: 0.88 },
        { name: "Model Deployment & ONNX", frequency: 74, modelWeight: 0.65, marketWeight: 0.78 },
        { name: "Linear Algebra & Calculus", frequency: 68, modelWeight: 0.90, marketWeight: 0.68 },
        { name: "CUDA & GPU Optimization", frequency: 54, modelWeight: 0.50, marketWeight: 0.62 }
      ]
    },
    skillNodes: [
      { id: "s1", label: "Python Core & NumPy", category: "Foundation", level: "Intermediate", mastery: 75, status: "Verified", deps: [] },
      { id: "s2", label: "Linear Algebra & Vector Calculus", category: "Foundation", level: "Foundational", mastery: 40, status: "Verified", deps: [] },
      { id: "s3", label: "Probability & Statistics", category: "Foundation", level: "Foundational", mastery: 25, status: "Available", deps: ["s2"] },
      { id: "s4", label: "PyTorch Tensor Operations", category: "Core Framework", level: "Intermediate", mastery: 20, status: "In Progress", deps: ["s1", "s2"] },
      { id: "s5", label: "Neural Network Fundamentals", category: "Core ML", level: "Intermediate", mastery: 0, status: "Available", deps: ["s3", "s4"] },
      { id: "s6", label: "CNN Architectures (ResNet/YOLO)", category: "Specialization", level: "Advanced", mastery: 0, status: "Locked", deps: ["s5"] },
      { id: "s7", label: "Vision Transformers (ViT)", category: "Specialization", level: "Advanced", mastery: 0, status: "Locked", deps: ["s6"] },
      { id: "s8", label: "Model Inference & Quantization", category: "Deployment", level: "Advanced", mastery: 0, status: "Locked", deps: ["s6"] }
    ],
    phases: [
      {
        id: "p1",
        phaseNum: 1,
        title: "Mathematical Foundations & Tensor Math",
        durationWeeks: 4,
        hoursTotal: 40,
        skillCoverage: ["Linear Algebra", "PyTorch Tensors", "Probability"],
        resources: [
          {
            id: "r101",
            title: "PyTorch 2.0 Zero to Mastery: Deep Learning",
            provider: "FreeCodeCamp / Daniel Bourke",
            url: "https://www.youtube.com/watch?v=V_xro1bcauA",
            duration: "12 hrs",
            format: "Video + Code",
            type: "Video Course",
            targetSkillId: "s4",
            targetSkillName: "PyTorch Tensor Operations",
            requiredSkills: ["Python Core & NumPy"],
            trustScore: {
              overall: 96,
              linkHealth: "100% Active",
              recency: "Updated 2024",
              authority: "Peer Verified (4.9/5)",
              crossSource: "High Agreement"
            },
            reasonCodes: [
              "ZERO_PREREQUISITE_VIOLATION",
              "HIGHEST_MARKET_WEIGHT (0.94)",
              "MATCHES_TIME_BUDGET (10h/w)",
              "100% FREE_OPEN_ACCESS"
            ],
            counterfactual: "Rejected Coursera Deep Learning Specialization ($49/mo) due to strict zero-cost budget constraint.",
            completionState: "Verified" // Verified, Completed, Opened, Unread
          },
          {
            id: "r102",
            title: "3Blue1Brown: Essence of Linear Algebra",
            provider: "3Blue1Brown Open Media",
            url: "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
            duration: "4 hrs",
            format: "Visual Interactive",
            type: "Video Series",
            targetSkillId: "s2",
            targetSkillName: "Linear Algebra & Vector Calculus",
            requiredSkills: [],
            trustScore: {
              overall: 99,
              linkHealth: "100% Active",
              recency: "Evergreen",
              authority: "Stanford/MIT Recommended",
              crossSource: "Consensus Baseline"
            },
            reasonCodes: [
              "BRIDGES_FOUNDATIONAL_GAP",
              "VISUAL_GEOMETRIC_INTUITION",
              "ZERO_COST"
            ],
            counterfactual: "Selected over MIT 18.06 textbook to fit 4-week phase horizon.",
            completionState: "Verified"
          },
          {
            id: "r103",
            title: "Probability & Statistics for Machine Learning",
            provider: "MIT OpenCourseWare 6.041",
            url: "https://ocw.mit.edu/courses/6-041-probabilistic-systems-analysis-and-applied-probability-fall-2010/",
            duration: "14 hrs",
            format: "Lectures & Problem Sets",
            type: "Academic Course",
            targetSkillId: "s3",
            targetSkillName: "Probability & Statistics",
            requiredSkills: ["Linear Algebra & Vector Calculus"],
            trustScore: {
              overall: 94,
              linkHealth: "100% Active",
              recency: "Curated 2023",
              authority: "MIT Academic Press",
              crossSource: "High Agreement"
            },
            reasonCodes: [
              "PREREQUISITE_SATISFIED (Linear Algebra Verified)",
              "ADDRESSES_PRIMARY_BOTTLENECK",
              "OPEN_ACCESS"
            ],
            counterfactual: "Prioritized over Khan Academy due to deeper rigour required for PyTorch loss function math.",
            completionState: "Opened"
          }
        ]
      },
      {
        id: "p2",
        phaseNum: 2,
        title: "Deep Learning & Convolutional Neural Networks",
        durationWeeks: 8,
        hoursTotal: 80,
        skillCoverage: ["Neural Network Fundamentals", "CNN Architectures", "PyTorch Practice"],
        resources: [
          {
            id: "r201",
            title: "Practical Deep Learning for Coders (v5)",
            provider: "Fast.ai / Jeremy Howard",
            url: "https://course.fast.ai/",
            duration: "25 hrs",
            format: "Interactive Code Notebooks",
            type: "Interactive Course",
            targetSkillId: "s5",
            targetSkillName: "Neural Network Fundamentals",
            requiredSkills: ["PyTorch Tensor Operations", "Probability & Statistics"],
            trustScore: {
              overall: 98,
              linkHealth: "100% Active",
              recency: "Updated 2024",
              authority: "Fast.ai Research",
              crossSource: "Industry Gold Standard"
            },
            reasonCodes: [
              "TOP_RATED_PROJECT_BASED",
              "EXCELLENT_PYTORCH_ALIGNMENT",
              "COMMUNITY_VERIFIED"
            ],
            counterfactual: "Chosen over CS231n due to immediate hands-on GPU notebook integration.",
            completionState: "Unread"
          },
          {
            id: "r202",
            title: "Stanford CS231n: Deep Learning for Computer Vision",
            provider: "Stanford University",
            url: "http://cs231n.stanford.edu/",
            duration: "20 hrs",
            format: "Video + Course Notes",
            type: "Academic Course",
            targetSkillId: "s6",
            targetSkillName: "CNN Architectures (ResNet/YOLO)",
            requiredSkills: ["Neural Network Fundamentals"],
            trustScore: {
              overall: 95,
              linkHealth: "100% Active",
              recency: "Updated 2023",
              authority: "Stanford AI Lab",
              crossSource: "High Agreement"
            },
            reasonCodes: [
              "RIGOROUS_ARCHITECTURE_THEORY",
              "EXPLAINS_RESNET_SKIP_CONNECTIONS"
            ],
            counterfactual: "Deferred to Phase 2 until PyTorch Tensor Ops mastery is verified.",
            completionState: "Unread"
          }
        ]
      },
      {
        id: "p3",
        phaseNum: 3,
        title: "Advanced Vision Transformers & Edge Inference",
        durationWeeks: 6,
        hoursTotal: 60,
        skillCoverage: ["Vision Transformers", "ONNX Model Export", "CUDA Basics"],
        resources: [
          {
            id: "r301",
            title: "Hugging Face Computer Vision Course",
            provider: "Hugging Face",
            url: "https://huggingface.co/learn/computer-vision-course/",
            duration: "15 hrs",
            format: "Interactive Code & Models",
            type: "Hands-on Guide",
            targetSkillId: "s7",
            targetSkillName: "Vision Transformers (ViT)",
            requiredSkills: ["CNN Architectures (ResNet/YOLO)"],
            trustScore: {
              overall: 97,
              linkHealth: "100% Active",
              recency: "Updated 2024",
              authority: "Hugging Face Core Team",
              crossSource: "Cutting Edge Standards"
            },
            reasonCodes: [
              "HIGH_MARKET_DEMAND (ViT & Fine-tuning)",
              "OPEN_SOURCE_ECOSYSTEM"
            ],
            counterfactual: "Requires CNN completion before unlocking.",
            completionState: "Unread"
          }
        ]
      }
    ],
    diagnostics: [
      {
        id: "q1",
        skillId: "s4",
        skillName: "PyTorch Tensor Operations",
        level: "Intermediate",
        question: "In PyTorch, what is the output shape of `torch.randn(2, 3, 4).transpose(1, 2)`?",
        options: [
          "(2, 4, 3)",
          "(3, 2, 4)",
          "(4, 3, 2)",
          "(2, 3, 4)"
        ],
        correctIndex: 0,
        explanation: "`transpose(1, 2)` swaps dimension 1 (size 3) with dimension 2 (size 4), yielding (2, 4, 3).",
        masteryImpact: 25
      },
      {
        id: "q2",
        skillId: "s3",
        skillName: "Probability & Statistics",
        level: "Foundational",
        question: "Which matrix transformation ensures covariance matrices in multivariate Gaussians are positive semi-definite?",
        options: [
          "Cholesky Decomposition (L Lᵀ)",
          "LU Factorization",
          "Singular Value Shift",
          "Gram-Schmidt Orthogonalization"
        ],
        correctIndex: 0,
        explanation: "Cholesky decomposition splits symmetric positive-definite covariance matrices into L Lᵀ.",
        masteryImpact: 20
      },
      {
        id: "q3",
        skillId: "s5",
        skillName: "Neural Network Fundamentals",
        level: "Intermediate",
        question: "Why do residual connections in ResNet prevent the vanishing gradient problem during backpropagation?",
        options: [
          "The identity shortcut `F(x) + x` creates a direct path `∂(x)/∂x = 1` for gradients to flow backwards unimpeded.",
          "They replace ReLU activation functions with Softmax.",
          "They reduce the number of parameters by half.",
          "They normalize batch activations to zero mean."
        ],
        correctIndex: 0,
        explanation: "Addition of `x` guarantees gradient addition `∂F/∂x + 1`, ensuring gradients never diminish to zero.",
        masteryImpact: 30
      }
    ],
    checkpoints: [
      {
        id: "cp1",
        skillId: "s4",
        skillName: "PyTorch Tensor Operations",
        title: "Checkpoint 1: Vectorized Tensor Ops & Custom Autograd Engine",
        instructions: "Implement a custom mini Autograd tensor engine in PyTorch/Python without using high-level `nn.Module`. Provide a clean GitHub repository or code snippet.",
        rubric: [
          { criterion: "Matrix & Tensor Shape Correctness", weight: 30 },
          { criterion: "Correct Backward Pass Computation", weight: 40 },
          { criterion: "Memory Efficiency & Vectorization", weight: 20 },
          { criterion: "Documentation & Clean Code", weight: 10 }
        ]
      }
    ]
  },
  {
    id: "data-eng",
    title: "SQL → Data Engineer",
    role: "Data Engineer",
    track: "Data & Warehousing",
    spec: "Specialization: Distributed Pipelines & Analytics Engineering",
    icon: "database",
    prompt: "I want to follow the SQL → Data Engineer route. I have solid database fundamentals. I can commit 10 hours per week and want an optimized milestone roadmap.",
    baselines: [
      { name: "SQL", level: "Intermediate", score: 70, color: "tertiary" },
      { name: "Python", level: "Foundational", score: 40, color: "secondary" }
    ],
    commitment: 10,
    horizon: 5,
    sprints: 20,
    format: "Interactive Labs",
    language: "English",
    budgetType: "Freemium",
    budgetCap: 100,
    bottleneck: "Distributed Query Optimization & Airflow DAGs — Needed to run production pipelines reliably.",
    marketPulse: {
      sampleSize: 3120,
      updatedDate: "Today (Live Feed)",
      demandTrend: "+22.1% Q/Q",
      avgSalary: "$135,000 - $175,000 / yr",
      topSkills: [
        { name: "Apache Spark & PySpark", frequency: 94, modelWeight: 0.90, marketWeight: 0.95 },
        { name: "SQL & Analytics Engineering (dbt)", frequency: 89, modelWeight: 0.85, marketWeight: 0.91 },
        { name: "Apache Airflow Orchestration", frequency: 82, modelWeight: 0.75, marketWeight: 0.84 },
        { name: "Data Lakes (Delta/Iceberg)", frequency: 71, modelWeight: 0.65, marketWeight: 0.76 }
      ]
    },
    skillNodes: [
      { id: "de1", label: "Advanced SQL & Indexing", category: "Core SQL", level: "Intermediate", mastery: 80, status: "Verified", deps: [] },
      { id: "de2", label: "Python Data Processing (Polars)", category: "Core Programming", level: "Foundational", mastery: 50, status: "Verified", deps: [] },
      { id: "de3", label: "Data Modeling (Kimball/Star Schema)", category: "Architecture", level: "Intermediate", mastery: 30, status: "Available", deps: ["de1"] },
      { id: "de4", label: "Distributed Systems & PySpark", category: "Big Data", level: "Intermediate", mastery: 15, status: "In Progress", deps: ["de2"] },
      { id: "de5", label: "Airflow Workflow Orchestration", category: "Pipelines", level: "Advanced", mastery: 0, status: "Locked", deps: ["de3", "de4"] }
    ],
    phases: [
      {
        id: "dep1",
        phaseNum: 1,
        title: "SQL Analytics Engineering & Star Schema",
        durationWeeks: 3,
        hoursTotal: 30,
        skillCoverage: ["Advanced SQL", "Data Modeling", "dbt Fundamentals"],
        resources: [
          {
            id: "der101",
            title: "dbt Fundamentals & Analytics Engineering",
            provider: "dbt Labs Official",
            url: "https://courses.getdbt.com/courses/dbt-fundamentals",
            duration: "8 hrs",
            format: "Interactive Course",
            type: "Official Certification",
            targetSkillId: "de3",
            targetSkillName: "Data Modeling (Kimball/Star Schema)",
            requiredSkills: ["Advanced SQL & Indexing"],
            trustScore: {
              overall: 99,
              linkHealth: "100% Active",
              recency: "Updated 2024",
              authority: "dbt Official Creator",
              crossSource: "Industry Standard"
            },
            reasonCodes: [
              "PREREQUISITE_SATISFIED (Advanced SQL Verified)",
              "FREE_OFFICIAL_CERT",
              "HIGH_MARKET_DEMAND"
            ],
            counterfactual: "Chosen over static SQL books due to hands-on dbt Cloud lab environment.",
            completionState: "Verified"
          }
        ]
      }
    ],
    diagnostics: [
      {
        id: "deq1",
        skillId: "de3",
        skillName: "Data Modeling",
        level: "Intermediate",
        question: "In Kimball dimensional modeling, what characterizes a Factless Fact Table?",
        options: [
          "A table that records events or relationships without any numeric measurement columns (e.g. student attendance).",
          "A table with no foreign keys.",
          "A table stored purely in memory.",
          "A staging table before ETL."
        ],
        correctIndex: 0,
        explanation: "Factless fact tables track occurrences (such as attendance or enrollment) where no numeric measure exists.",
        masteryImpact: 25
      }
    ],
    checkpoints: []
  },
  {
    id: "llm-app",
    title: "Frontend → LLM Apps",
    role: "LLM Application Engineer",
    track: "GenAI Track",
    spec: "Specialization: RAG, Embeddings & Vector Architectures",
    icon: "code_blocks",
    prompt: "I want to transition from Frontend to LLM Apps. I know TypeScript and web interfaces. I can commit 10 hours per week and want to build robust AI products.",
    baselines: [
      { name: "TypeScript / JS", level: "Intermediate", score: 80, color: "tertiary" },
      { name: "REST APIs & Async", level: "Proficient", score: 75, color: "tertiary" }
    ],
    commitment: 10,
    horizon: 4,
    sprints: 16,
    format: "Video + Code",
    language: "English",
    budgetType: "Free only",
    budgetCap: 0,
    bottleneck: "Vector Embeddings & Context Retrieval Optimization — Needed to prevent hallucination in production apps.",
    marketPulse: {
      sampleSize: 1980,
      updatedDate: "Today (Live Feed)",
      demandTrend: "+34.5% Q/Q",
      avgSalary: "$140,000 - $190,000 / yr",
      topSkills: [
        { name: "Vector DBs (Pinecone / Qdrant)", frequency: 95, modelWeight: 0.92, marketWeight: 0.96 },
        { name: "LangChain / LlamaIndex", frequency: 88, modelWeight: 0.85, marketWeight: 0.90 },
        { name: "Prompt Engineering & Guardrails", frequency: 79, modelWeight: 0.70, marketWeight: 0.81 }
      ]
    },
    skillNodes: [
      { id: "llm1", label: "TypeScript Async & Streaming", category: "Core Web", level: "Intermediate", mastery: 85, status: "Verified", deps: [] },
      { id: "llm2", label: "Vector Embeddings & Semantic Search", category: "AI Core", level: "Foundational", mastery: 35, status: "In Progress", deps: ["llm1"] },
      { id: "llm3", label: "RAG Architecture & Chunking", category: "Architecture", level: "Intermediate", mastery: 10, status: "Available", deps: ["llm2"] },
      { id: "llm4", label: "Evaluations & LLM Tracing", category: "Production", level: "Advanced", mastery: 0, status: "Locked", deps: ["llm3"] }
    ],
    phases: [
      {
        id: "llmp1",
        phaseNum: 1,
        title: "Vector DBs, Embeddings & RAG Fundamentals",
        durationWeeks: 3,
        hoursTotal: 30,
        skillCoverage: ["Embeddings", "Cosine Similarity", "Pinecone/Qdrant"],
        resources: [
          {
            id: "llmr101",
            title: "Building Production RAG Systems",
            provider: "DeepLearning.AI / Andrew Ng",
            url: "https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/",
            duration: "5 hrs",
            format: "Video + Jupyter Labs",
            type: "Interactive Short Course",
            targetSkillId: "llm3",
            targetSkillName: "RAG Architecture & Chunking",
            requiredSkills: ["Vector Embeddings & Semantic Search"],
            trustScore: {
              overall: 99,
              linkHealth: "100% Active",
              recency: "Updated 2024",
              authority: "DeepLearning.AI",
              crossSource: "Industry Benchmark"
            },
            reasonCodes: [
              "PREREQUISITE_SATISFIED",
              "HIGHEST_EMBEDDING_PRACTICE",
              "ZERO_COST"
            ],
            counterfactual: "Chosen over generic YouTube tutorials for verified evaluation rubric.",
            completionState: "Opened"
          }
        ]
      }
    ],
    diagnostics: [],
    checkpoints: []
  }
];

export const INITIAL_USER_STATE = {
  activeProfileId: "ml-cv",
  userEmail: "aamina.hasan@apogee.ai",
  userName: "Aamina Hasan",
  currentStep: 1, // 1: Intake, 2: Diagnostic, 3: Route & Graph, 4: Career Pack
  routeOptimizationMode: "Balanced", // Balanced, Fast, Deep
  graphViewMode: "skills", // skills vs courses
  readinessBand: { min: 68, max: 76 }, // Range per N6 & FR12
  hoursCompleted: 16,
  hoursTotal: 180,
  weeksRemaining: 18,
  targetEta: "March 15, 2027",
  routeChangeReceipts: [
    {
      id: "rc1",
      timestamp: "Yesterday 14:32",
      trigger: "Completed PyTorch 2.0 Quiz (Verified)",
      change: "Unlocked 2 dependent CNN modules in Phase 2",
      reasonCodes: ["VERIFIED_PROOF_ACCEPTED", "PREREQUISITE_UNLOCKED"]
    }
  ]
};
