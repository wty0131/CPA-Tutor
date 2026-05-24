import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Typography, Spin } from "antd";
import {
  BookOutlined,
  CloseCircleOutlined,
  QuestionCircleOutlined,
  TrophyOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { fetchSubjects } from "../api/subjects";
import type { Subject } from "../api/subjects";
import { fetchWrongStats } from "../api/wrongbook";

const { Title } = Typography;

export default function Dashboard() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [stats, setStats] = useState({ total: 0, due_for_review: 0 });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([fetchSubjects(), fetchWrongStats()])
      .then(([subj, st]) => {
        setSubjects(subj);
        setStats(st);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  const totalQuestions = subjects.reduce((s, subj) => s + subj.question_count, 0);

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>CPA 学习仪表盘</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="总题目数" value={totalQuestions} prefix={<QuestionCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="错题本" value={stats.total} prefix={<CloseCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="待复习" value={stats.due_for_review} prefix={<BookOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="科目数" value={6} prefix={<TrophyOutlined />} /></Card>
        </Col>
      </Row>
      <Title level={3}>科目分类</Title>
      <Row gutter={[16, 16]}>
        {subjects.map((s) => (
          <Col key={s.id} xs={24} sm={12} md={8}>
            <Card
              hoverable
              title={`${s.code} ${s.name}`}
              onClick={() => navigate(`/subject/${s.id}`)}
              style={{ minHeight: 160 }}
            >
              <p>{s.description}</p>
              <Row gutter={16}>
                <Col span={12}><Statistic title="题目" value={s.question_count} /></Col>
                <Col span={12}><Statistic title="错题" value={s.wrong_count} valueStyle={{ color: s.wrong_count > 0 ? "#cf1322" : "#3f8600" }} /></Col>
              </Row>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
