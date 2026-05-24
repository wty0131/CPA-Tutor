import { useEffect, useState } from "react";
import { Card, Button, Select, Typography, Table, Tag, Space, message, Spin, Statistic, Row, Col } from "antd";
import { CloudDownloadOutlined, ReloadOutlined } from "@ant-design/icons";
import api from "../api/client";

const { Title } = Typography;

export default function Admin() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>(undefined);
  const [scraping, setScraping] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = () => {
    setLoading(true);
    Promise.all([
      api.get("/api/subjects").then((r) => setSubjects(r.data)),
      api.get("/api/scraper/status").then((r) => setStatus(r.data)),
    ]).finally(() => setLoading(false));
  };

  const handleScrape = async () => {
    setScraping(true);
    try {
      const { data } = await api.post("/api/scraper/trigger", {
        subject_code: selectedSubject || null,
      });
      message.success(`抓取完成！获取 ${data.total_fetched} 题，入库 ${data.saved} 题`);
      loadStatus();
    } catch (e) {
      message.error("抓取失败");
    } finally {
      setScraping(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <Title level={2}>题库管理</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="题库总量" value={status?.total_questions || 0} />
            <Button onClick={loadStatus} icon={<ReloadOutlined />} size="small" style={{ marginTop: 8 }}>刷新</Button>
          </Card>
        </Col>
      </Row>

      {status?.by_subject && (
        <Table
          dataSource={status.by_subject}
          pagination={false}
          columns={[
            { title: "科目", dataIndex: "subject", key: "subject" },
            { title: "题目数", dataIndex: "count", key: "count" },
          ]}
          style={{ marginBottom: 24 }}
        />
      )}

      <Card title="手动抓取">
        <Space>
          <Select
            placeholder="选择科目（留空=全部）"
            allowClear
            style={{ width: 240 }}
            value={selectedSubject}
            onChange={setSelectedSubject}
          >
            {subjects.map((s) => (
              <Select.Option key={s.code} value={s.code}>{s.code} {s.name}</Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<CloudDownloadOutlined />}
            loading={scraping}
            onClick={handleScrape}
          >
            开始抓取
          </Button>
        </Space>
        <div style={{ marginTop: 12, fontSize: 12, color: "#888" }}>
          注意：当前使用 Demo 爬虫。接入真实题库网站请修改 scraper/sites/ 目录下的爬虫配置。
        </div>
      </Card>
    </div>
  );
}
