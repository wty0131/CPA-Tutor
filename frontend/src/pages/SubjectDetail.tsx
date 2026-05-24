import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card, Button, List, Tag, Spin, Typography, Row, Col, Space, Tree,
} from "antd";
import { PlayCircleOutlined, BookOutlined, ApartmentOutlined } from "@ant-design/icons";
import { fetchSubject } from "../api/subjects";
import { fetchQuestions } from "../api/questions";
import { fetchKnowledgePoints } from "../api/knowledge";

const { Title, Paragraph } = Typography;

export default function SubjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [subject, setSubject] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [kps, setKps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      fetchSubject(+id),
      fetchQuestions({ subject_id: +id, page_size: 10 }),
      fetchKnowledgePoints({ subject_id: +id }),
    ])
      .then(([subj, qData, kpData]) => {
        setSubject(subj);
        setQuestions(qData.items || []);
        setKps(kpData || []);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;
  if (!subject) return <div>科目未找到</div>;

  const treeData = kps.map((kp: any) => ({
    title: `${kp.name} (${kp.question_count}题)`,
    key: kp.id,
    children: kp.children?.map((c: any) => ({
      title: `${c.name} (${c.question_count}题)`,
      key: c.id,
    })),
  }));

  const typeColors: Record<string, string> = {
    single_choice: "blue",
    multi_choice: "purple",
    calculation: "orange",
    essay: "green",
  };
  const typeNames: Record<string, string> = {
    single_choice: "单选",
    multi_choice: "多选",
    calculation: "计算",
    essay: "简答",
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>{subject.code} {subject.name}</Title>
      <Paragraph>{subject.description}</Paragraph>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}><Card><Statistic title="题库数量" value={subject.question_count} /></Card></Col>
        <Col span={8}><Card><Statistic title="知识点" value={subject.knowledge_point_count} /></Card></Col>
      </Row>

      <Row gutter={16}>
        <Col span={10}>
          <Card title="知识点树" extra={<Button icon={<ApartmentOutlined />} size="small" onClick={() => navigate(`/knowledge/${id}`)}>查看详情</Button>}>
            <Tree treeData={treeData} defaultExpandAll />
          </Card>
        </Col>
        <Col span={14}>
          <Card
            title="题目列表"
            extra={
              <Space>
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => navigate(`/practice/${id}`)}>开始练习</Button>
                <Button icon={<BookOutlined />} onClick={() => navigate(`/wrongbook?subject=${id}`)}>错题本</Button>
              </Space>
            }
          >
            <List
              dataSource={questions}
              renderItem={(q: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Tag color={typeColors[q.type]}>{typeNames[q.type]}</Tag>
                        难度: {q.difficulty}/5
                        <span>{q.stem.slice(0, 50)}...</span>
                      </Space>
                    }
                    description={
                      <Space>
                        {q.knowledge_points?.map((kp: any) => (
                          <Tag key={kp.id}>{kp.name}</Tag>
                        ))}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
