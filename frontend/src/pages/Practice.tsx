import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card, Button, Radio, Checkbox, Space, Tag, Typography, Modal,
  Spin, Result, Progress, Select, Empty,
} from "antd";
import {
  CheckCircleOutlined, CloseCircleOutlined,
  BulbOutlined, ArrowRightOutlined,
} from "@ant-design/icons";
import { fetchQuestions } from "../api/questions";
import { submitAnswer } from "../api/practice";

const { Title, Paragraph } = Typography;

export default function Practice() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<any[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string>("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  // Filter state
  const [type, setType] = useState<string | undefined>(undefined);
  const [difficulty, setDifficulty] = useState<number | undefined>(undefined);

  const loadQuestions = (typeFilter?: string, diffFilter?: number) => {
    setLoading(true);
    const params: any = { page_size: 50 };
    if (subjectId) params.subject_id = +subjectId;
    if (typeFilter) params.type = typeFilter;
    if (diffFilter) params.difficulty = diffFilter;
    fetchQuestions(params).then((data) => {
      setQuestions(data.items || []);
      setCurrentIdx(0);
      setResult(null);
      setSelectedAnswer("");
      setShowExplanation(false);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadQuestions();
  }, [subjectId]);

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  if (questions.length === 0) {
    return (
      <div style={{ padding: 24 }}>
        <Empty description="暂无题目，请先触发爬取或导入题目" />
        <Button onClick={() => navigate("/")} style={{ marginTop: 16 }}>返回首页</Button>
      </div>
    );
  }

  const question = questions[currentIdx];
  const progress = ((currentIdx + 1) / questions.length * 100);

  const handleSubmit = async () => {
    if (!selectedAnswer || submitting) return;
    setSubmitting(true);
    const data = await submitAnswer(question.id, selectedAnswer);
    setResult(data);
    setShowExplanation(true);
    setSubmitting(false);
  };

  const handleNext = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1);
      setSelectedAnswer("");
      setResult(null);
      setShowExplanation(false);
    }
  };

  const typeNames: Record<string, string> = {
    single_choice: "单选", multi_choice: "多选", calculation: "计算", essay: "简答",
  };

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Space>
          <Select placeholder="题型筛选" allowClear style={{ width: 120 }} value={type} onChange={(v) => { setType(v); loadQuestions(v, difficulty); }}>
            <Select.Option value="single_choice">单选</Select.Option>
            <Select.Option value="multi_choice">多选</Select.Option>
            <Select.Option value="calculation">计算</Select.Option>
            <Select.Option value="essay">简答</Select.Option>
          </Select>
          <Select placeholder="难度筛选" allowClear style={{ width: 120 }} value={difficulty} onChange={(v) => { setDifficulty(v); loadQuestions(type, v); }}>
            {[1, 2, 3, 4, 5].map((d) => <Select.Option key={d} value={d}>难度 {d}</Select.Option>)}
          </Select>
        </Space>
        <Tag color="blue">第 {currentIdx + 1} / {questions.length} 题</Tag>
      </div>

      <Progress percent={progress} style={{ marginBottom: 16 }} showInfo={false} />

      <Card>
        <Space style={{ marginBottom: 12 }}>
          <Tag color="blue">{typeNames[question.type]}</Tag>
          <Tag>难度 {question.difficulty}</Tag>
          <Tag>{question.subject_name}</Tag>
          {question.knowledge_points?.map((kp: any) => (
            <Tag key={kp.id} color="green">{kp.name}</Tag>
          ))}
        </Space>

        <Title level={4}>{question.stem}</Title>

        <div style={{ margin: "16px 0" }}>
          {question.type === "multi_choice" ? (
            <Checkbox.Group
              value={selectedAnswer ? selectedAnswer.split(",") : []}
              onChange={(vals) => setSelectedAnswer((vals as string[]).sort().join(","))}
              disabled={!!result}
            >
              <Space direction="vertical">
                {question.options?.map((opt: any) => (
                  <Checkbox key={opt.label} value={opt.label}>
                    <strong>{opt.label}.</strong> {opt.text}
                  </Checkbox>
                ))}
              </Space>
            </Checkbox.Group>
          ) : (
            <Radio.Group value={selectedAnswer} onChange={(e) => setSelectedAnswer(e.target.value)} disabled={!!result}>
              <Space direction="vertical">
                {question.options?.map((opt: any) => (
                  <Radio key={opt.label} value={opt.label}>
                    <strong>{opt.label}.</strong> {opt.text}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          )}
        </div>

        {result && (
          <Result
            status={result.correct ? "success" : "error"}
            title={result.correct ? "回答正确!" : `回答错误! 正确答案: ${result.correct_answer}`}
            icon={result.correct ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          />
        )}

        {showExplanation && result?.explanation && (
          <Card
            title={<><BulbOutlined /> AI 解析</>}
            style={{ marginTop: 16, background: "#f6ffed" }}
          >
            <Paragraph>{result.explanation}</Paragraph>
            {result.knowledge_points?.length > 0 && (
              <div>
                <strong>关联知识点：</strong>
                {result.knowledge_points.map((kp: any) => (
                  <Tag key={kp.id} color="green">{kp.name}</Tag>
                ))}
              </div>
            )}
          </Card>
        )}

        <div style={{ marginTop: 16, textAlign: "right" }}>
          <Space>
            {!result ? (
              <Button type="primary" onClick={handleSubmit} loading={submitting} disabled={!selectedAnswer}>
                提交答案
              </Button>
            ) : (
              <Button type="primary" icon={<ArrowRightOutlined />} onClick={handleNext} disabled={currentIdx >= questions.length - 1}>
                下一题
              </Button>
            )}
            <Button onClick={() => navigate(-1)}>返回</Button>
          </Space>
        </div>
      </Card>
    </div>
  );
}
