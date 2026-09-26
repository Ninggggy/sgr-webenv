package org.expasy.cellosaurus.formats.xml;
import org.junit.jupiter.api.Test;
import org.expasy.cellosaurus.genomics.str.Species;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
class StreamRobustnessTest {
 private List<String> parse(int chunk) throws IOException {
  for (Species s: Species.values()) s.getCellLines().clear();
  InputStream src=getClass().getClassLoader().getResourceAsStream("cellosaurus_head_1000.xml");
  new XmlParser().parse(new FilterInputStream(src){public int read(byte[] b,int off,int len)throws IOException{return super.read(b,off,Math.min(chunk,len));}});
  List<String> out=new ArrayList<>();
  for (Species s: Species.values()) s.getCellLines().forEach(c->out.add(c.getAccession()+"|"+c.getName()+"|"+c.getProblem()));
  return out;
 }
 @Test void inputChunkBoundariesDoNotAlterIdentities() throws IOException {assertEquals(parse(8192),parse(1));}
 @Test void malformedXmlFailsClosed(){assertThrows(IOException.class,()->new XmlParser().parse(new ByteArrayInputStream("<cellosaurus><broken>".getBytes(StandardCharsets.UTF_8))));}
 @Test void externalEntitiesRejected(){assertThrows(IOException.class,()->new XmlParser().parse(new ByteArrayInputStream("<!DOCTYPE x [<!ENTITY ex SYSTEM 'file:///etc/passwd'>]><x>&ex;</x>".getBytes(StandardCharsets.UTF_8))));}
 @Test void sourcesAreScopedToMarkerDataInBothXmlFormats() throws IOException {
  for (String tag : Arrays.asList("alleles", "marker-alleles")) {
   for (Species sp : Species.values()) sp.getCellLines().clear();
   String xml = "<cellosaurus><cell-line><accession>CVCL_TEST</accession><name type='identifier'>Source scope fixture</name>"
    + "<species-list><cv-term>Homo sapiens</cv-term></species-list><str-list><source-list><source>GLOBAL</source></source-list><marker-list>"
    + "<marker id='D7S820' conflict='true'><marker-data-list><marker-data><" + tag + ">8,10</" + tag + ">"
    + "<source-list><reference-list><reference resource-internal-ref='PubMed=123'/></reference-list></source-list></marker-data></marker-data-list></marker>"
    + "<marker id='vWA' conflict='false'><marker-data-list><marker-data><" + tag + ">17,19</" + tag + "></marker-data></marker-data-list></marker>"
    + "</marker-list></str-list></cell-line></cellosaurus>";
   new XmlParser().parse(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)));
   assertEquals(1, Species.HUMAN.getCellLines().size());
   for (org.expasy.cellosaurus.genomics.str.Profile profile : Species.HUMAN.getCellLines().get(0).getProfiles()) {
    for (org.expasy.cellosaurus.genomics.str.Marker marker : profile.getMarkers()) {
     assertEquals(marker.getName().equals("D7S820") ? Collections.singleton("PubMed=123") : Collections.emptySet(), marker.getSources());
    }
   }
  }
 }
}
