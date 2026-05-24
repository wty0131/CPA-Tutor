import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Card, List, Tag, Button, Space, Typography, Rate, Spin, Popconfirm, Empty, Progress,
} from "antd";
import { DeleteOutlined, BookOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { fetchWrongAnswers, reviewWrongAnswer, deleteWrongAnswer } from "../api/wrongbook";

const { Title, Paragraph } = Typography;

export default function WrongBook() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const subjectId = searchParams.get("subject") || undefined;
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    fetchWrongAnswers({
      subject_id: subjectId ? +subjectId : undefined,
      page_size: 50,
    }).then((data) => setItems(data.items || [])).finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, [subjectId]);

  const handleReview = async (id: number, quality: number) => {
    await reviewWrongAnswer(id, quality);
    loadData();
  };

  const handleDelete = async (id: number) => {
    await deleteWrongAnswer(id);
    loadData();
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <Title level={2}>
        <BookOutlined /> 错题本
      </Title>
      <Paragraph type="secondary">
        按 SM-2 算法安排间隔复习，到期的优先展示。给复习质量打分后自动计算下次复习时间。
      </Paragraph>

      {items.length === 0 ? (
        <Empty description="错题本为空，继续保持！" />
      ) : (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Space key="review">
                  <span style={{ fontSize: 12, color: "#888" }}>
                    掌握度: <Progress type="circle" percent={item.mastery_level} size={24} />
                  </span>
                  <Rate count={5} defaultValue={3} style={{ fontSize: 16 }} onChange={(v) => handleReview(item.id, v)} />
                </Space>,
                <Popconfirm key="del" title="确定移出错题本？" onConfirm={() => handleDelete(item.id)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Tag color="red">{item.subject_name}</Tag>
                    <span style={{ cursor: "pointer" }} onClick={() => navigate(`/practice/${item.id}`)}>
                      {item.stem.slice(0, 60)}...
                    </span>
                  </Space>
                }
                description={
                  <Space>
                    <Tag>你的答案: {item.user_answer}</Tag>
                    <Tag color="green">正确答案: {item.correct_answer}</Tag>
                    <span style={{ fontSize: 12, color: "#888" }}>
                      复习{item.review_count}次 · 下次复习: {new Date(item.next_review).toLocaleDateString()}
                    </span>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
}
