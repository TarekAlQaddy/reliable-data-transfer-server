public class Packet {
    private int checksum;
    private int seq_no;
    private int is_last_packet;
    private boolean is_ack;
    private String data;

    Packet(int checksum, int seq_no, int is_last_packet, boolean is_ack) {
        this.checksum = checksum;
        this.seq_no = seq_no;
        this.is_last_packet = is_last_packet;
        this.is_ack = is_ack;
    }

    Packet(int checksum, int seq_no, int is_last_packet, boolean is_ack, String data) {
        this.checksum = checksum;
        this.seq_no = seq_no;
        this.is_last_packet = is_last_packet;
        this.is_ack = is_ack;
        this.data = data;
    }

    int getChecksum() {
        return checksum;
    }

    public void setChecksum(int checksum) {
        this.checksum = checksum;
    }

    int getSeq_no() {
        return seq_no;
    }

    public void setSeq_no(int seq_no) {
        this.seq_no = seq_no;
    }

    int getIsLastPacket() {
        return is_last_packet;
    }

    public void setIsLastPacket(int no_of_pkts) {
        this.is_last_packet = no_of_pkts;
    }

    boolean isIs_ack() {
        return is_ack;
    }

    public void setIs_ack(boolean is_ack) {
        this.is_ack = is_ack;
    }

    String getData() {
        return data;
    }

    void setData(String data) {
        this.data = data;
    }
}
