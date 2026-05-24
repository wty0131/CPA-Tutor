import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card, Tree, Typography, Spin, Tag, List, Button, Space, Collapse, Empty,
} from "antd";
import { BulbOutlined, BookOutlined, PlayCircleOutlined } from "@ant-design/icons";
import {
  fetchKnowledgePoints, fetchKnowledgePoint, summarizeKnowledgePoint,
} from "../api/knowledge";

const { Title, Paragraph } = Typography;

export default function KnowledgeTree() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const navigate = useNavigate();

  const [kps, setKps] = useState<any[]>([]);
  const [selectedKp, setSelectedKp] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [summarizing, setSummarizing] = useState(false);

  useEffect(() => {
    fetchKnowledgePoints({ subject_id: subjectId ? +subjectId : undefined })
      .then((data) => setKps(data || []))
      .finally(() => setLoading(false));
  }, [subjectId]);

  const handleSelect = async (selectedKeys: React.Key[]) => {
    if (selectedKeys.length === 0) return;
    const kpId = selectedKeys[0] as number;
    const data = await fetchKnowledgePoint(kpId);
    setSelectedKp(data);
  };

  const handleSummarize = async () => {
    if (!selectedKp) return;
    setSummarizing(true);
    const data = await summarizeKnowledgePoint(selectedKp.id);
    setSelectedKp({ ...selectedKp, ...data, summary: data.ai_result?.summary || data.summary });
    setSummarizing(false);
  };

  const treeData = kps.map((kp: any) => ({
    title: kp.name,
    key: kp.id,
    children: kp.children?.map((c: any) => ({
      title: c.name,
      key: c.id,
    })),
  }));

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", gap: 16 }}>
        <Card title="知识点树" style={{ width: 350, flexShrink: 0 }}>
          {treeData.length > 0 ? (
            <Tree
              treeData={treeData}
              onSelect={handleSelect}
              defaultExpandAll
            />
          ) : (
            <Empty description="暂无知识点数据" />
          )}
        </Card>

        <Card style={{ flex: 1 }} title={selectedKp ? selectedKp.name : "请选择知识点"}>
          {selectedKp ? (
            <>
              <Space style={{ marginBottom: 16 }}>
                <Button icon={<PlayCircleOutlined />} onClick={() => navigate(`/practice/${selectedKp.subject_id}`)}>
                  练习相关题目
                </Button>
                <Button icon={<BulbOutlined />} loading={summarizing} onClick={handleSummarize}>
                  AI 归纳总结
                </Button>
              </Space>

              {selectedKp.summary && (
                <Collapse
                  style={{ marginTop: 16 }}
                  items={[{
                    key: "summary",
                    label: "AI 归纳总结",
                    children: <Paragraph>{selectedKp.summary}</Paragraph>,
                  }]}
                />
              )}

              {selectedKp.key_concepts && (
                <div style={{ marginTop: 16 }}>
                  <Title level={5}>核心概念</Title>
                  <Space wrap>
                    {selectedKp.key_concepts.map((c: string, i: number) => (
                      <Tag key={i} color="blue">{c}</Tag>
                    ))}
                  </Space>
                </div>
              )}

              {selectedKp.common_mistakes && (
                <div style={{ marginTop: 16 }}>
                  <Title level={5}>常见错误</Title>
                  <List dataSource={selectedKp.common_mistakes} renderItem={(item: string) => <List.Item>{item}</List.Item>} />
                </div>
              )}

              {selectedKp.questions && (
                <div style={{ marginTop: 16 }}>
                  <Title level={5}>关联题目</Title>
                  <List
                    dataSource={selectedKp.questions}
                    renderItem={(q: any) => (
                      <List.Item>
                        <List.Item.Meta
                          title={<span>{q.stem.slice(0, 80)}...</span>}
                          description={<Tag>难度 {q.difficulty}</Tag>}
                        />
                      </List.Item>
                    )}
                  />
                </div>
              )}
            </>
          ) : (
            <Empty description="点击左侧知识点查看详情" />
          )}
        </Card>
      </div>
    </div>
  );
}
