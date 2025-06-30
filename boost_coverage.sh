#!/bin/bash
echo "🚀 提升 OTEL 覆盖率到 80%+"
echo "=========================="

# 备份当前测试文件
cp tests/test_otel_helpers.py tests/test_otel_helpers.py.before_boost

# 添加高级覆盖率测试到现有文件末尾
cat >> tests/test_otel_helpers.py << 'TESTEOF'


# =================== 覆盖率提升测试 ===================
class TestAdvancedCoverage:
    """专门测试未覆盖的代码路径"""
    
    def test_span_manager_zero_tokens_cost(self):
        """测试零tokens情况 - 避免除零错误"""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        span_manager = SpanManager(mock_tracer)
        
        cost_info = {
            "cost_usd": 0.01,
            "model": "test",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        span_manager.set_cost_attributes(mock_span, cost_info)
        
        # 验证没有除零错误，且没有prompt_ratio
        mock_span.set_attributes.assert_called_once()
        attributes = mock_span.set_attributes.call_args[0][0]
        assert "tokens.prompt_ratio" not in attributes
    
    def test_span_manager_pr_url_edge_cases(self):
        """测试PR URL边缘情况"""
        mock_tracer = MagicMock()
        
        # 测试无效PR号码
        span_manager = SpanManager(mock_tracer, "https://github.com/owner/repo/pull/not-a-number")
        assert "pr.url" in span_manager.pr_metadata
        assert "pr.number" not in span_manager.pr_metadata
    
    def test_span_manager_risk_level_mapping(self):
        """测试所有风险级别映射"""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        span_manager = SpanManager(mock_tracer)
        
        risk_tests = [("low", 1), ("medium", 4), ("high", 7), ("critical", 10), ("unknown", 0)]
        
        for risk_level, expected_score in risk_tests:
            mock_span.reset_mock()
            result_info = {"summary": {"risk_level": risk_level}}
            span_manager.set_result_attributes(mock_span, result_info)
            attributes = mock_span.set_attributes.call_args[0][0]
            assert attributes["risk.score"] == expected_score
    
    def test_operation_instrumentor_no_span_manager(self):
        """测试无span_manager的操作仪器"""
        op_instrumentor = OperationInstrumentor(None, "test-op")
        
        # 这些调用应该安全
        op_instrumentor.set_cost_info({"cost": 0.01})
        op_instrumentor.set_result_info({"issues": []})
        op_instrumentor.set_custom_attributes({"attr": "value"})
        
        with op_instrumentor as op:
            assert op is not None
            assert op.span is None
    
    def test_manager_shutdown_exception(self):
        """测试关闭异常处理"""
        manager = OTELManager()
        mock_processor = MagicMock()
        mock_processor.force_flush.side_effect = Exception("Flush failed")
        manager.span_processor = mock_processor
        
        # 应该不抛出异常
        manager.shutdown()
        mock_processor.force_flush.assert_called_once()
TESTEOF

echo "🧪 运行增强测试..."
python -m pytest tests/test_otel_helpers.py -v --cov=monitoring.otel_helpers --cov-report=term-missing --cov-report=html:htmlcov

echo "📊 覆盖率分析完成!"
echo "查看报告: open htmlcov/index.html"
