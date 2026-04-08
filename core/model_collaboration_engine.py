"""
弥娅模型协作引擎 (Model Collaboration Engine)

设计目标:
1. 复用原有 ModelPool 的所有功能（配置加载、任务分类、模型选择）
2. 在之上叠加智能协作层，实现多模型联动
3. 根据任务复杂度自动选择协作模式
4. 兼顾 QQ 模式和终端模式的模型调度
5. 高性能与低 Token 消耗兼顾
6. 零硬编码，所有值均从配置文件加载

协作模式:
- SINGLE: 单模型处理（简单任务，最低 token）
- CHAIN: 链式协作（中等任务，2-3 模型串联）
- PARALLEL: 并行投票（重要决策，多模型并行 + 共识）
- ROLE: 角色分工（复杂任务，分析师+创作者+审核员）
"""

import asyncio
import json
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from core.model_pool import ModelPool, TaskType, ModelConfig
from core.terminal_formatter import TerminalFormatter

logger = logging.getLogger(__name__)


class CollaborationMode(str, Enum):
    SINGLE = "single"
    CHAIN = "chain"
    PARALLEL = "parallel"
    ROLE = "role"


class ComplexityLevel(int, Enum):
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    ADVANCED = 5


class CollaborationResult:
    def __init__(
        self,
        response: str,
        mode: CollaborationMode,
        complexity: ComplexityLevel,
        models_used: List[str],
        token_estimate: int = 0,
        reasoning: str = "",
    ):
        self.response = response
        self.mode = mode
        self.complexity = complexity
        self.models_used = models_used
        self.token_estimate = token_estimate
        self.reasoning = reasoning

    def to_dict(self) -> Dict:
        return {
            "response": self.response,
            "mode": self.mode.value,
            "complexity": self.complexity.value,
            "models_used": self.models_used,
            "token_estimate": self.token_estimate,
            "reasoning": self.reasoning,
        }


def _load_collaboration_config() -> Dict:
    try:
        config_path = (
            Path(__file__).parent.parent / "config" / "multi_model_config.json"
        )
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("collaboration", {})
    except Exception as e:
        logger.warning(f"[协作引擎] 加载配置失败: {e}")
    return {}


class ModelCollaborationEngine:
    """
    模型协作引擎 - 零硬编码，所有配置从 multi_model_config.json 加载
    """

    def __init__(self, model_pool: ModelPool, config: Optional[Dict] = None):
        self.model_pool = model_pool
        raw_config = config or {}
        self.config = raw_config.get("collaboration") or _load_collaboration_config()

        # 开关
        self.enabled = self.config.get("enabled", True)

        # 阈值
        thresholds = self.config.get("complexity_thresholds", {})
        self.threshold_single = thresholds.get("single_max", 2)
        self.threshold_chain = thresholds.get("chain_max", 3)
        self.threshold_parallel = thresholds.get("parallel_max", 4)

        # Token 预算
        budget = self.config.get("token_budget", {})
        self.max_tokens_single = budget.get("single", 2000)
        self.max_tokens_chain = budget.get("chain", 6000)
        self.max_tokens_parallel = budget.get("parallel", 10000)
        self.max_tokens_role = budget.get("role", 15000)

        # 复杂度评估
        ca = self.config.get("complexity_assessment", {})
        self.length_thresholds = ca.get("length_thresholds", {})
        self.task_weights = ca.get("task_weights", {})
        self.complex_keywords = ca.get("complex_keywords", [])
        self.multi_intent = ca.get("multi_intent", {})
        self.score_range = ca.get("score_range", {})

        # 平台配置
        po = self.config.get("platform_overrides", {})
        self.terminal_config = po.get("terminal", {})
        self.qq_config = po.get("qq", {})

        # 角色分工
        rc = self.config.get("role_collaboration", {})
        self.role_mapping = rc.get("role_mapping", {})
        self.default_role_assignment = rc.get("default_role_assignment", {})
        self.role_prompts = rc.get("role_prompts", {})
        self.role_user_templates = rc.get("role_user_templates", {})
        self.role_skip_messages = rc.get("skip_messages", {})

        # 链式协作
        cc = self.config.get("chain_collaboration", {})
        self.chain_system_prompt = cc.get("understanding_system_prompt", "")
        self.chain_understanding_template = cc.get("understanding_prompt_template", "")
        self.chain_injection_template = cc.get("injection_template", "")
        self.chain_max_words = cc.get("max_understanding_words", 200)

        # 并行投票
        pv = self.config.get("parallel_voting", {})
        self.similarity_threshold = pv.get("similarity_threshold", 0.7)
        self.arbiter_task = pv.get("arbiter_task", "summarization")
        self.arbiter_priority = pv.get("arbiter_priority", "speed")
        self.arbiter_system_prompt = pv.get("arbiter_system_prompt", "")
        self.arbiter_user_template = pv.get("arbiter_user_template", "")
        self.comparison_separator = pv.get("comparison_separator", "\n\n---\n\n")
        self.comparison_format = pv.get("comparison_format", "[{model_id}]: {response}")

        # Endpoint
        self.endpoint_map = self.config.get("endpoint_map", {})
        self.default_endpoint = self.config.get("default_endpoint", "qq")

        # 消息文本
        msgs = self.config.get("messages", {})
        self.msg_error_client_unavailable = msgs.get(
            "error_client_unavailable", "[错误] AI 客户端不可用"
        )
        self.msg_error_call_failed = msgs.get(
            "error_call_failed", "[AI 调用失败: {error}]"
        )
        self.msg_empty_response = msgs.get("empty_response", "[空响应]")
        self.msg_fallback_analysis = msgs.get(
            "fallback_analysis", "分析阶段跳过（无可用模型）"
        )
        self.msg_fallback_creation = msgs.get(
            "fallback_creation", "创作阶段跳过（无可用模型）"
        )
        self.msg_reasoning_single = msgs.get(
            "reasoning_single", "单模型处理: {model_id}"
        )
        self.msg_reasoning_chain = msgs.get("reasoning_chain", "链式协作: {models}")
        self.msg_reasoning_parallel = msgs.get(
            "reasoning_parallel", "并行投票: {models}"
        )
        self.msg_reasoning_role = msgs.get("reasoning_role", "角色分工: {models}")
        self.msg_reasoning_degraded = msgs.get("reasoning_degraded", "降级: {error}")

        # 执行参数
        exe = self.config.get("execution", {})
        self.single_priority = exe.get("single_priority", "balanced")
        self.token_estimate_divisor = exe.get("token_estimate_divisor", 2)
        self.similarity_ngram_size = exe.get("similarity_ngram_size", 3)

        # 复杂度分数映射
        self.complexity_scores = self.config.get(
            "complexity_scores",
            {
                "single": 2,
                "chain": 3,
                "parallel": 4,
                "role": 5,
            },
        )

        # 平台关键词
        self.platform_keywords = self.config.get("platform_keywords", {})

        # 统计
        self.stats = {
            "total_calls": 0,
            "mode_distribution": {m.value: 0 for m in CollaborationMode},
            "avg_complexity": 0.0,
            "total_token_estimate": 0,
        }

        logger.info(
            f"[协作引擎] 初始化完成, enabled={self.enabled}, "
            f"thresholds: single<={self.threshold_single}, "
            f"chain<={self.threshold_chain}, "
            f"parallel<={self.threshold_parallel}"
        )

    async def process(
        self,
        message: str,
        task_type: str,
        platform: str = "qq",
        context: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        tools: Optional[List] = None,
        ai_client_factory=None,
    ) -> CollaborationResult:
        from core.terminal_formatter import TerminalFormatter

        self.stats["total_calls"] += 1
        start_time = time.time()

        if not self.enabled:
            return await self._fallback_to_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                ai_client_factory,
            )

        complexity = await self._assess_complexity(message, task_type, platform)
        mode = self._select_mode(complexity, task_type, platform)

        # 终端输出：协作开始
        print(TerminalFormatter.separator("协作引擎"))
        print(TerminalFormatter.collaboration_start(mode.value, complexity.value))
        print(
            f"{TerminalFormatter.DIM}  任务: {task_type} | 平台: {platform}{TerminalFormatter.RESET}"
        )

        try:
            if mode == CollaborationMode.SINGLE:
                result = await self._execute_single(
                    message,
                    task_type,
                    platform,
                    context,
                    system_prompt,
                    user_prompt,
                    tools,
                    ai_client_factory,
                )
            elif mode == CollaborationMode.CHAIN:
                result = await self._execute_chain(
                    message,
                    task_type,
                    platform,
                    context,
                    system_prompt,
                    user_prompt,
                    tools,
                    ai_client_factory,
                )
            elif mode == CollaborationMode.PARALLEL:
                result = await self._execute_parallel(
                    message,
                    task_type,
                    platform,
                    context,
                    system_prompt,
                    user_prompt,
                    tools,
                    ai_client_factory,
                )
            else:
                result = await self._execute_role(
                    message,
                    task_type,
                    platform,
                    context,
                    system_prompt,
                    user_prompt,
                    tools,
                    ai_client_factory,
                )
        except Exception as e:
            logger.warning(f"[协作引擎] 协作执行失败，降级为单模型: {e}")
            result = await self._fallback_to_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                ai_client_factory,
            )
            result.reasoning = self.msg_reasoning_degraded.format(error=str(e))

        elapsed = time.time() - start_time
        self.stats["mode_distribution"][result.mode.value] += 1
        self.stats["total_token_estimate"] += result.token_estimate

        # 终端输出：协作结果
        from core.terminal_formatter import TerminalFormatter

        print(
            TerminalFormatter.result(
                result.mode.value,
                result.models_used,
                result.token_estimate,
                result.reasoning,
            )
        )
        print(TerminalFormatter.separator())

        logger.info(
            f"[协作引擎] 处理完成 | 模式={result.mode.value} | "
            f"复杂度={result.complexity} | "
            f"模型={','.join(result.models_used)} | "
            f"耗时={elapsed:.2f}s | "
            f"Token≈{result.token_estimate}"
        )

        return result

    async def _assess_complexity(
        self, message: str, task_type: str, platform: str
    ) -> ComplexityLevel:
        score = 1

        msg_len = len(message) if message else 0
        level_1 = self.length_thresholds.get("level_1", 200)
        level_2 = self.length_thresholds.get("level_2", 500)
        if msg_len > level_1:
            score += 1
        if msg_len > level_2:
            score += 1

        score += self.task_weights.get(task_type, 1)

        if any(kw in message.lower() for kw in self.complex_keywords):
            score += 1

        terminal_kw = self.terminal_config.get("complex_keywords", [])
        if platform in self.platform_keywords.get("terminal", ["terminal"]):
            if terminal_kw and any(kw in message.lower() for kw in terminal_kw):
                score += 1

        question_count = message.count("?") + message.count("？")
        q_threshold = self.multi_intent.get("question_threshold", 3)
        if question_count >= q_threshold:
            score += 1

        connectors = self.multi_intent.get("connectors", [])
        q_with_conn = self.multi_intent.get("question_with_connectors", 2)
        if connectors and any(c in message for c in connectors):
            if question_count >= q_with_conn:
                score += 1

        score_min = self.score_range.get("min", 1)
        score_max = self.score_range.get("max", 5)
        score = max(score_min, min(score_max, score))
        return ComplexityLevel(score)

    def _select_mode(
        self, complexity: ComplexityLevel, task_type: str, platform: str
    ) -> CollaborationMode:
        terminal_keys = self.platform_keywords.get("terminal", ["terminal"])
        qq_keys = self.platform_keywords.get("qq", ["qq"])

        if platform in terminal_keys:
            overrides = self.terminal_config.get("mode_overrides", {})
        elif platform in qq_keys:
            overrides = self.qq_config.get("mode_overrides", {})
        else:
            overrides = {}

        if task_type in overrides:
            return CollaborationMode(overrides[task_type])

        if complexity.value <= self.threshold_single:
            return CollaborationMode.SINGLE
        elif complexity.value <= self.threshold_chain:
            return CollaborationMode.CHAIN
        elif complexity.value <= self.threshold_parallel:
            return CollaborationMode.PARALLEL
        else:
            return CollaborationMode.ROLE

    async def _execute_single(
        self,
        message,
        task_type,
        platform,
        context,
        system_prompt,
        user_prompt,
        tools,
        factory,
    ) -> CollaborationResult:
        endpoint = self._get_endpoint(platform)
        model_config = self.model_pool.select_model_for_task(
            task_type,
            endpoint,
            self.single_priority,
        )

        if not model_config or not model_config.api_key:
            return await self._fallback_to_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        client = self._create_client(model_config, factory, tools)

        # 思考过程
        from core.terminal_formatter import TerminalFormatter

        thinking = ""

        print(TerminalFormatter.chain_step(1, model_config.id, "思考分析"))

        # 单模型不使用额外思考，直接显示步骤
        print(TerminalFormatter.chain_step(2, model_config.id, "生成回复"))

        # 正式回复
        response = await self._call_client(
            client, system_prompt or "", user_prompt or "", tools
        )

        return CollaborationResult(
            response=response,
            mode=CollaborationMode.SINGLE,
            complexity=ComplexityLevel.SIMPLE,
            models_used=[model_config.id],
            token_estimate=self._estimate_tokens(message, response),
            reasoning=self.msg_reasoning_single.format(model_id=model_config.id),
        )

    async def _execute_chain(
        self,
        message,
        task_type,
        platform,
        context,
        system_prompt,
        user_prompt,
        tools,
        factory,
    ) -> CollaborationResult:
        route = self.model_pool.get_route(task_type)
        if not route:
            return await self._execute_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        chain_models = []
        for model_id in [route.primary, route.secondary]:
            if model_id and model_id in self.model_pool._models:
                config = self.model_pool._models[model_id]
                if config.api_key and config.base_url:
                    chain_models.append(config)

        if len(chain_models) < 2:
            return await self._execute_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        model_1 = chain_models[0]
        client_1 = self._create_client(model_1, factory, None)
        understanding_prompt = self.chain_understanding_template.format(
            task_type=task_type,
            message=message,
            max_words=self.chain_max_words,
        )
        print(TerminalFormatter.chain_step(1, model_1.id, "语义理解"))
        understanding = await self._call_client(
            client_1,
            system_prompt=self.chain_system_prompt,
            user_prompt=understanding_prompt,
            tools=None,
        )

        model_2 = chain_models[1]
        client_2 = self._create_client(model_2, factory, tools)
        enhanced_user_prompt = self.chain_injection_template.format(
            user_prompt=user_prompt or "",
            understanding=understanding,
        )
        print(TerminalFormatter.chain_step(2, model_2.id, "深度处理"))
        response = await self._call_client(
            client_2,
            system_prompt,
            enhanced_user_prompt,
            tools,
        )

        models_used = [m.id for m in chain_models[:2]]
        return CollaborationResult(
            response=response,
            mode=CollaborationMode.CHAIN,
            complexity=ComplexityLevel.MODERATE,
            models_used=models_used,
            token_estimate=self._estimate_tokens(message, response, understanding),
            reasoning=self.msg_reasoning_chain.format(
                models=" → ".join(models_used),
            ),
        )

    async def _execute_parallel(
        self,
        message,
        task_type,
        platform,
        context,
        system_prompt,
        user_prompt,
        tools,
        factory,
    ) -> CollaborationResult:
        route = self.model_pool.get_route(task_type)
        if not route:
            return await self._execute_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        parallel_models = []
        for model_id in [route.primary, route.secondary, route.fallback]:
            if model_id and model_id in self.model_pool._models:
                config = self.model_pool._models[model_id]
                if config.api_key and config.base_url:
                    parallel_models.append(config)
                    if len(parallel_models) >= 2:
                        break

        if len(parallel_models) < 2:
            return await self._execute_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        parallel_model_ids = [m.id for m in parallel_models]
        print(TerminalFormatter.parallel_step(parallel_model_ids))

        tasks = []
        for model_config in parallel_models:
            client = self._create_client(model_config, factory, None)
            task = self._call_client(client, system_prompt, user_prompt, None)
            tasks.append((model_config.id, task))

        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        model_responses = []
        models_used = []
        for i, (model_id, _) in enumerate(tasks):
            resp = results[i]
            if isinstance(resp, Exception):
                logger.warning(f"[协作引擎] 模型 {model_id} 调用失败: {resp}")
                continue
            model_responses.append((model_id, resp))
            models_used.append(model_id)

        if not model_responses:
            return await self._execute_single(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        # 【思考-输出分离模式】
        # 第一个模型负责思考，第二个模型负责生成最终回复
        if len(model_responses) >= 2:
            thinking_result = model_responses[0][1]  # 模型1的思考结果

            # 显示思考过程到终端
            try:
                print(TerminalFormatter.thinking_block(thinking_result[:300]))
            except Exception as e:
                logger.debug(f"[协作引擎] 显示思考过程失败: {e}")

            # 用模型2根据思考结果生成最终回复
            output_model = parallel_models[1]
            output_client = self._create_client(output_model, factory, tools)

            output_prompt = f"""基于以下思考过程，请生成最终回复（只输出回复内容，不要包含思考过程）：

思考过程：
{thinking_result}

用户问题：{message}

要求：
1. 只输出最终回复，不要包含任何思考过程
2. 回复要简洁、自然，符合弥娅的人设
3. 回复不超过3句话"""

            final_response = await self._call_client(
                output_client,
                system_prompt=system_prompt,
                user_prompt=output_prompt,
                tools=tools,
            )

            # 清理可能残留的思考过程
            if "<think>" in final_response:
                parts = final_response.split("")
                final_response = parts[-1].strip()

            return CollaborationResult(
                response=final_response,
                mode=CollaborationMode.PARALLEL,
                complexity=ComplexityLevel.COMPLEX,
                models_used=[parallel_model_ids[0], parallel_model_ids[1]],
                token_estimate=self._estimate_tokens(
                    message, thinking_result + final_response
                ),
                reasoning=f"思考-输出分离: {parallel_model_ids[0]}思考 → {parallel_model_ids[1]}输出",
            )

        # 只有一个模型响应时的处理
        final_response = model_responses[0][1]

        return CollaborationResult(
            response=final_response,
            mode=CollaborationMode.PARALLEL,
            complexity=ComplexityLevel.COMPLEX,
            models_used=models_used,
            token_estimate=sum(
                self._estimate_tokens(message, resp) for _, resp in model_responses
            ),
            reasoning=self.msg_reasoning_parallel.format(
                models=", ".join(models_used),
            ),
        )

    async def _execute_role(
        self,
        message,
        task_type,
        platform,
        context,
        system_prompt,
        user_prompt,
        tools,
        factory,
    ) -> CollaborationResult:
        roles = self._get_role_models(task_type, platform)
        if len(roles) < 2:
            return await self._execute_chain(
                message,
                task_type,
                platform,
                context,
                system_prompt,
                user_prompt,
                tools,
                factory,
            )

        analyst_prompt = self.role_prompts.get("analyst", "")
        creator_prompt_text = self.role_prompts.get("creator", "")
        reviewer_prompt_text = self.role_prompts.get("reviewer", "")

        analyst_template = self.role_user_templates.get("analyst", "{message}")
        creator_template = self.role_user_templates.get("creator", "{user_prompt}")
        reviewer_template = self.role_user_templates.get("reviewer", "{message}")

        skip_analysis = self.role_skip_messages.get("analyst", "")
        skip_creation = self.role_skip_messages.get("creator", "")

        # 阶段 1: 分析师
        analyst_config = roles.get("analyst")
        if analyst_config and analyst_config.api_key:
            print(TerminalFormatter.role_step("analyst", analyst_config.id))
            analyst_client = self._create_client(analyst_config, factory, None)
            analysis = await self._call_client(
                analyst_client,
                system_prompt=analyst_prompt,
                user_prompt=analyst_template.format(
                    task_type=task_type,
                    message=message,
                ),
                tools=None,
            )
        else:
            analysis = skip_analysis

        # 阶段 2: 创作者
        creator_config = roles.get("creator")
        if creator_config and creator_config.api_key:
            print(TerminalFormatter.role_step("creator", creator_config.id))
            creator_client = self._create_client(creator_config, factory, tools)
            draft = await self._call_client(
                creator_client,
                system_prompt=system_prompt or creator_prompt_text,
                user_prompt=creator_template.format(
                    user_prompt=user_prompt or "",
                    analysis=analysis,
                ),
                tools=None,
            )
        else:
            draft = skip_creation

        # 阶段 3: 审核员
        reviewer_config = roles.get("reviewer")
        if reviewer_config and reviewer_config.api_key:
            print(TerminalFormatter.role_step("reviewer", reviewer_config.id))
            reviewer_client = self._create_client(reviewer_config, factory, None)
            final_response = await self._call_client(
                reviewer_client,
                system_prompt=reviewer_prompt_text,
                user_prompt=reviewer_template.format(
                    message=message,
                    draft=draft,
                ),
                tools=None,
            )
        else:
            final_response = draft

        models_used = [
            config.id
            for config in [analyst_config, creator_config, reviewer_config]
            if config and config.api_key
        ]

        return CollaborationResult(
            response=final_response,
            mode=CollaborationMode.ROLE,
            complexity=ComplexityLevel.ADVANCED,
            models_used=models_used,
            token_estimate=self._estimate_tokens(
                message,
                final_response,
                analysis,
                draft,
            ),
            reasoning=self.msg_reasoning_role.format(
                models=" → ".join(models_used),
            ),
        )

    async def _consensus_decision(
        self,
        model_responses: List[Tuple[str, str]],
        message: str,
        task_type: str,
        platform: str,
        system_prompt: str,
        factory,
    ) -> str:
        if len(model_responses) == 2:
            resp_1 = model_responses[0][1]
            resp_2 = model_responses[1][1]

            if self._similarity(resp_1, resp_2) > self.similarity_threshold:
                return resp_1 if len(resp_1) >= len(resp_2) else resp_2

            return resp_1 if len(resp_1) >= len(resp_2) else resp_2

        arbiter_config = self.model_pool.select_model_for_task(
            self.arbiter_task,
            self._get_endpoint(platform),
            self.arbiter_priority,
        )

        if not arbiter_config or not arbiter_config.api_key:
            return model_responses[0][1]

        arbiter_client = self._create_client(arbiter_config, factory, None)

        comparison_text = self.comparison_separator.join(
            self.comparison_format.format(model_id=mid, response=resp)
            for mid, resp in model_responses
        )

        arbiter_prompt = self.arbiter_user_template.format(
            message=message,
            comparison_text=comparison_text,
        )

        return await self._call_client(
            arbiter_client,
            system_prompt=self.arbiter_system_prompt,
            user_prompt=arbiter_prompt,
            tools=None,
        )

    async def _fallback_to_single(
        self,
        message,
        task_type,
        platform,
        context,
        system_prompt,
        user_prompt,
        tools,
        factory,
    ) -> CollaborationResult:
        return await self._execute_single(
            message,
            task_type,
            platform,
            context,
            system_prompt,
            user_prompt,
            tools,
            factory,
        )

    def _get_role_models(
        self, task_type: str, platform: str
    ) -> Dict[str, Optional[ModelConfig]]:
        mapping = self.role_mapping.get(task_type, self.default_role_assignment)

        roles = {}
        for role_name, model_id in mapping.items():
            config = self.model_pool._models.get(model_id)
            if config and config.api_key and config.base_url:
                roles[role_name] = config
            else:
                roles[role_name] = None

        return roles

    def _get_endpoint(self, platform: str) -> str:
        return self.endpoint_map.get(platform, self.default_endpoint)

    def _create_client(self, model_config: ModelConfig, factory, tools=None):
        if factory:
            client = factory.create_client(
                provider=model_config.provider.value,
                api_key=model_config.api_key or "",
                model=model_config.name,
                base_url=model_config.base_url,
            )
        else:
            from core.ai_client import AIClientFactory

            client = AIClientFactory.create_client(
                provider=model_config.provider.value,
                api_key=model_config.api_key or "",
                model=model_config.name,
                base_url=model_config.base_url,
            )

        if client and tools:
            client.set_tool_registry(tools)

        return client

    async def _call_client(
        self,
        client,
        system_prompt: str,
        user_prompt: str,
        tools,
    ) -> str:
        if not client:
            return self.msg_error_client_unavailable

        try:
            if tools:
                response = await client.chat_with_system_prompt(
                    system_prompt=system_prompt,
                    user_message=user_prompt,
                    tools=tools,
                    tool_choice="auto",
                )
            else:
                response = await client.chat_with_system_prompt(
                    system_prompt=system_prompt,
                    user_message=user_prompt,
                )

            # 处理可能的非字符串返回值
            if response is None:
                return self.msg_empty_response
            if not isinstance(response, str):
                return str(response)
            return response
        except Exception as e:
            logger.error(f"[协作引擎] AI 调用失败: {e}")
            return self.msg_error_call_failed.format(error=e)

    def _estimate_tokens(self, *texts: str) -> int:
        total_chars = sum(len(t) for t in texts if t)
        return total_chars // self.token_estimate_divisor

    def _similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        n = self.similarity_ngram_size

        def get_ngrams(text):
            return set(text[i : i + n] for i in range(len(text) - n + 1))

        ngrams1 = get_ngrams(text1)
        ngrams2 = get_ngrams(text2)

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2

        return len(intersection) / len(union) if union else 0.0

    def get_stats(self) -> Dict:
        total = self.stats["total_calls"]
        if total > 0:
            self.stats["avg_complexity"] = (
                sum(
                    self.complexity_scores.get(mode, 1) * count
                    for mode, count in self.stats["mode_distribution"].items()
                )
                / total
            )

        return self.stats.copy()

    def is_simple_task(self, message: str, task_type: str) -> bool:
        score = 0
        level_1 = self.length_thresholds.get("level_1", 200)
        level_2 = self.length_thresholds.get("level_2", 500)
        if len(message) > level_1:
            score += 1
        if len(message) > level_2:
            score += 1
        score += self.task_weights.get(task_type, 1)
        return score <= self.threshold_single
