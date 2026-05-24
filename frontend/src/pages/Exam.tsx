import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card, Button, Radio, Checkbox, Space, Tag, Typography, Spin, Result,
  Row, Col, Statistic, Progress, Select, Modal, Divider, Table,
} from "antd";
import {
  ClockCircleOutlined, TrophyOutlined, ThunderboltOutlined,
  PieChartOutlined, WarningOutlined,
} from "@ant-design/icons";
import { generateExam, submitExam } from "../api/exam";

const { Title, Paragraph, Text } = Typography;

export default function Exam() {
  const navigate = useNavigate();

  const [phase, setPhase] = useState<"config" | "running" | "report">("config");
  const [subjectId, setSubjectId] = useState<number | undefined>(undefined);
  const [examData, setExamData] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [report, setReport] = useState<any>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  const startExam = async () => {
    setLoading(true);
    const data = await generateExam(subjectId || undefined);
    setExamData(data);
    setTimeLeft(data.duration_minutes * 60);
    setAnswers({});
    setReport(null);
    setPhase("running");
    setLoading(false);

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  useEffect(() => {
    if (timeLeft === 0 && phase === "running" && examData) {
      handleSubmit();
    }
  }, [timeLeft]);

  const handleAnswer = (qid: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [String(qid)]: value }));
  };

  const handleSubmit = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setLoading(true);
    const data = await submitExam(answers);
    setReport(data);
    setPhase("report");
    setLoading(false);
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  };

  const answeredCount = Object.keys(answers).length;

  // ---- Config Screen ----
  if (phase === "config") {
    return (
      <div style={{ padding: 24, maxWidth: 500, margin: "100px auto" }}>
        <Card>
          <Title level={3}><TrophyOutlined /> CPA 模拟考试</Title>
          <Paragraph type="secondary">
            真实考试模式：单选15题 + 多选5题 + 计算5题，计时完成，自动评分。
          </Paragraph>
          <div style={{ margin: "16px 0" }}>
            <Text>选择科目（留空=综合出题）：</Text>
            <Select
              placeholder="全部科目"
              allowClear
              style={{ width: "100%", marginTop: 8 }}
              value={subjectId}
              onChange={setSubjectId}
            >
              {[
                { id: 1, name: "会计" }, { id: 2, name: "审计" },
                { id: 3, name: "财务成本管理" }, { id: 4, name: "税法" },
                { id: 5, name: "经济法" }, { id: 6, name: "公司战略与风险管理" },
              ].map((s) => <Select.Option key={s.id} value={s.id}>{s.name}</Select.Option>)}
            </Select>
          </div>
          <Button type="primary" size="large" block loading={loading} onClick={startExam}>
            开始考试
          </Button>
        </Card>
      </div>
    );
  }

  // ---- Running ----
  if (phase === "running" && examData) {
    return (
      <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
        <div style={{ position: "sticky", top: 0, zIndex: 100, background: "#fff", padding: "12px 16px", borderRadius: 8, marginBottom: 16, boxShadow: "0 2px 8px rgba(0,0,0,0.1)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Space size="large">
            <Tag color={timeLeft < 300 ? "red" : "blue"} icon={<ClockCircleOutlined />} style={{ fontSize: 18, padding: "4px 12px" }}>
              {formatTime(timeLeft)}
            </Tag>
            <Text>{answeredCount}/{examData.total} 已答</Text>
            <Progress percent={Math.round(answeredCount / examData.total * 100)} style={{ width: 100 }} showInfo={false} />
          </Space>
          <Button type="primary" danger onClick={handleSubmit} loading={loading}>
            交卷
          </Button>
        </div>

        {examData.questions.map((q: any, idx: number) => (
          <Card key={q.id} style={{ marginBottom: 16 }}>
            <Space style={{ marginBottom: 8 }}>
              <Tag color="blue">{idx + 1}</Tag>
              <Tag>{q.type === "single_choice" ? "单选" : q.type === "multi_choice" ? "多选" : q.type === "calculation" ? "计算" : q.type}</Tag>
              <Tag color="green">{q.subject_name}</Tag>
            </Space>
            <Paragraph strong>{q.stem}</Paragraph>
            {q.type === "multi_choice" ? (
              <Checkbox.Group
                value={answers[String(q.id)] ? answers[String(q.id)].split(",") : []}
                onChange={(vals) => handleAnswer(q.id, (vals as string[]).sort().join(","))}
              >
                <Space direction="vertical">
                  {q.options?.map((opt: any) => (
                    <Checkbox key={opt.label} value={opt.label}><strong>{opt.label}.</strong> {opt.text}</Checkbox>
                  ))}
                </Space>
              </Checkbox.Group>
            ) : (
              <Radio.Group
                value={answers[String(q.id)]}
                onChange={(e) => handleAnswer(q.id, e.target.value)}
              >
                <Space direction="vertical">
                  {q.options?.map((opt: any) => (
                    <Radio key={opt.label} value={opt.label}><strong>{opt.label}.</strong> {opt.text}</Radio>
                  ))}
                </Space>
              </Radio.Group>
            )}
          </Card>
        ))}

        <div style={{ textAlign: "center", padding: 16 }}>
          <Button type="primary" size="large" onClick={handleSubmit} loading={loading}>
            交卷并查看成绩
          </Button>
        </div>
      </div>
    );
  }

  // ---- Report ----
  if (phase === "report" && report) {
    const typeColors: Record<string, string> = {
      single_choice: "blue", multi_choice: "purple", calculation: "orange",
    };
    const typeNames: Record<string, string> = {
      single_choice: "单选", multi_choice: "多选", calculation: "计算",
    };

    return (
      <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
        <Card>
          <Result
            status={report.score >= 60 ? "success" : "error"}
            title={`${report.score} 分`}
            subTitle={`${report.correct}/${report.total} 正确 | ${report.score >= 60 ? '&#x2705; 通过' : '&#x274C; 未通过（60分及格）'}`}
          />
        </Card>

        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card title={<><PieChartOutlined /> 题型分析</>}>
              {Object.entries(report.type_breakdown).map(([t, s]: any) =>
                s.total > 0 ? (
                  <div key={t} style={{ marginBottom: 12 }}>
                    <Space>
                      <Tag color={typeColors[t]}>{typeNames[t]}</Tag>
                      <Text>{s.correct}/{s.total}</Text>
                      <Progress
                        percent={Math.round(s.correct / s.total * 100)}
                        size="small"
                        style={{ width: 120 }}
                        status={s.correct / s.total >= 0.6 ? "success" : "exception"}
                      />
                    </Space>
                  </div>
                ) : null
              )}
            </Card>
          </Col>
          <Col span={12}>
            <Card title={<><WarningOutlined /> 薄弱知识点</>}>
              {report.weak_knowledge_points.length === 0 ? (
                <Text type="secondary">全部正确，没有薄弱点！</Text>
              ) : (
                report.weak_knowledge_points.map((wk: any, i: number) => (
                  <div key={i} style={{ marginBottom: 8 }}>
                    <Tag color="red">{wk.subject}</Tag>
                    <Tag>{wk.knowledge_point}</Tag>
                    <Text type="danger">错{wk.wrong_count}次</Text>
                  </div>
                ))
              )}
            </Card>
          </Col>
        </Row>

        <Card title="题目解析" style={{ marginTop: 16 }}>
          {report.results.map((r: any, idx: number) => (
            <div key={r.question_id} style={{ marginBottom: 16, padding: 12, background: r.is_correct ? "#f6ffed" : "#fff2f0", borderRadius: 8 }}>
              <Space>
                <Tag color={r.is_correct ? "success" : "error"}>{idx + 1}</Tag>
                <Tag>{typeNames[r.type]}</Tag>
                <Text>{r.stem}...</Text>
              </Space>
              <div style={{ marginTop: 8 }}>
                <Text>你的答案：<Text type={r.is_correct ? "success" : "danger"} strong>{r.your_answer || "未答"}</Text></Text>
                {!r.is_correct && <Text> | 正确答案：<Text type="success" strong>{r.correct_answer}</Text></Text>}
              </div>
              {!r.is_correct && r.explanation && (
                <Paragraph style={{ marginTop: 8, background: "#fff", padding: 8, borderRadius: 4 }}>
                  {r.explanation}
                </Paragraph>
              )}
              {r.knowledge_points?.length > 0 && (
                <Space style={{ marginTop: 4 }}>
                  {r.knowledge_points.map((kp: any) => <Tag key={kp.id} color="green">{kp.name}</Tag>)}
                </Space>
              )}
            </div>
          ))}
        </Card>

        <div style={{ textAlign: "center", marginTop: 24 }}>
          <Space>
            <Button type="primary" size="large" onClick={() => setPhase("config")}>再来一场</Button>
            <Button size="large" onClick={() => navigate("/")}>返回首页</Button>
          </Space>
        </div>
      </div>
    );
  }

  return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;
}
